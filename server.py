#!/usr/bin/env python

# server stuff
from bottle import Bottle, route, get, post, error, run, template, static_file, request, response, FormsDict, redirect, template, HTTPResponse
import waitress
# monkey patching
import monkey
# rest of the project
import database
import htmlmodules
import htmlgenerators
import malojatime
import utilities
from utilities import resolveImage
from urihandler import uri_to_internal, remove_identical
import urihandler
import info
# doreah toolkit
from doreah import settings
from doreah.logging import log
# technical
from importlib.machinery import SourceFileLoader
import _thread
import sys
import signal
import os
import setproctitle
# url handling
import urllib



#settings.config(files=["settings/default.ini","settings/settings.ini"])
#settings.update("settings/default.ini","settings/settings.ini")
MAIN_PORT = settings.get_settings("WEB_PORT")
HOST = settings.get_settings("HOST")


webserver = Bottle()


import lesscpy
css = ""
for f in os.listdir("website/less"):
	css += lesscpy.compile("website/less/" + f)

os.makedirs("website/css",exist_ok=True)
with open("website/css/style.css","w") as f:
	f.write(css)


@webserver.route("")
@webserver.route("/")
def mainpage():
	response = static_html("start")
	return response

@webserver.error(400)
@webserver.error(403)
@webserver.error(404)
@webserver.error(405)
@webserver.error(408)
@webserver.error(500)
@webserver.error(505)
def customerror(error):
	code = int(str(error).split(",")[0][1:])
	log("HTTP Error: " + str(code),module="error")

	if os.path.exists("website/errors/" + str(code) + ".html"):
		return static_file("website/errors/" + str(code) + ".html",root="")
	else:
		with open("website/errors/generic.html") as htmlfile:
			html = htmlfile.read()

		# apply global substitutions
		with open("website/common/footer.html") as footerfile:
			footerhtml = footerfile.read()
		with open("website/common/header.html") as headerfile:
			headerhtml = headerfile.read()
		html = html.replace("</body>",footerhtml + "</body>").replace("</head>",headerhtml + "</head>")

		html = html.replace("ERROR_CODE",str(code))
		return html



def graceful_exit(sig=None,frame=None):
	#urllib.request.urlopen("http://[::1]:" + str(DATABASE_PORT) + "/sync")
	log("Received signal to shutdown")
	try:
		database.sync()
	except Exception as e:
		log("Error while shutting down!",e)
	log("Server shutting down...")
	os._exit(42)


@webserver.route("/image")
def dynamic_image():
	keys = FormsDict.decode(request.query)
	relevant, _, _, _ = uri_to_internal(keys)
	result = resolveImage(**relevant)
	if result == "": return ""
	redirect(result,307)

@webserver.route("/images/<pth:re:.*\\.jpeg>")
@webserver.route("/images/<pth:re:.*\\.jpg>")
@webserver.route("/images/<pth:re:.*\\.png>")
@webserver.route("/images/<pth:re:.*\\.gif>")
def static_image(pth):
	small_pth = pth + "-small"
	if os.path.exists("images/" + small_pth):
		response = static_file("images/" + small_pth,root="")
	else:
		try:
			from wand.image import Image
			img = Image(filename="images/" + pth)
			x,y = img.size[0], img.size[1]
			smaller = min(x,y)
			if smaller > 300:
				ratio = 300/smaller
				img.resize(int(ratio*x),int(ratio*y))
				img.save(filename="images/" + small_pth)
				response = static_file("images/" + small_pth,root="")
			else:
				response = static_file("images/" + pth,root="")
		except:
			response = static_file("images/" + pth,root="")

	#response = static_file("images/" + pth,root="")
	response.set_header("Cache-Control", "public, max-age=86400")
	return response

#@webserver.route("/<name:re:.*\\.html>")
@webserver.route("/<name:re:.*\\.js>")
@webserver.route("/<name:re:.*\\.css>")
@webserver.route("/<name:re:.*\\.less>")
@webserver.route("/<name:re:.*\\.png>")
@webserver.route("/<name:re:.*\\.jpeg>")
@webserver.route("/<name:re:.*\\.ico>")
@webserver.route("/<name:re:.*\\.txt>")
def static(name):
	response = static_file("website/" + name,root="")
	response.set_header("Cache-Control", "public, max-age=3600")
	return response

@webserver.route("/<name>")
def static_html(name):
	linkheaders = ["</css/style.css>; rel=preload; as=style"]
	keys = remove_identical(FormsDict.decode(request.query))

	pyhp_file = os.path.exists("website/" + name + ".pyhp")
	html_file = os.path.exists("website/" + name + ".html")
	pyhp_pref = settings.get_settings("USE_PYHP")


	# if a pyhp file exists, use this
	if (pyhp_file and pyhp_pref) or (pyhp_file and not html_file):
		from doreah.pyhp import file
		environ = {} #things we expose to the pyhp pages

		# maloja
		environ["db"] = database
		environ["htmlmodules"] = htmlmodules
		environ["htmlgenerators"] = htmlgenerators
		environ["malojatime"] = malojatime
		environ["utilities"] = utilities
		environ["urihandler"] = urihandler
		environ["info"] = info
		# external
		environ["urllib"] = urllib
		# request
		environ["filterkeys"], environ["limitkeys"], environ["delimitkeys"], environ["amountkeys"] = uri_to_internal(keys)

		#response.set_header("Content-Type","application/xhtml+xml")
		return file("website/" + name + ".pyhp",environ)

	# if not, use the old way
	else:

		with open("website/" + name + ".html") as htmlfile:
			html = htmlfile.read()

		# apply global substitutions
		with open("website/common/footer.html") as footerfile:
			footerhtml = footerfile.read()
		with open("website/common/header.html") as headerfile:
			headerhtml = headerfile.read()
		html = html.replace("</body>",footerhtml + "</body>").replace("</head>",headerhtml + "</head>")


		# If a python file exists, it provides the replacement dict for the html file
		if os.path.exists("website/" + name + ".py"):
			#txt_keys = SourceFileLoader(name,"website/" + name + ".py").load_module().replacedict(keys,DATABASE_PORT)
			try:
				txt_keys,resources = SourceFileLoader(name,"website/" + name + ".py").load_module().instructions(keys)
			except Exception as e:
				log("Error in website generation: " + str(sys.exc_info()),module="error")
				raise

			# add headers for server push
			for resource in resources:
				if all(ord(c) < 128 for c in resource["file"]):
					# we can only put ascii stuff in the http header
					linkheaders.append("<" + resource["file"] + ">; rel=preload; as=" + resource["type"])

			# apply key substitutions
			for k in txt_keys:
				if isinstance(txt_keys[k],list):
					# if list, we replace each occurence with the next item
					for element in txt_keys[k]:
						html = html.replace(k,element,1)
				else:
					html = html.replace(k,txt_keys[k])


		response.set_header("Link",",".join(linkheaders))

		return html
		#return static_file("website/" + name + ".html",root="")


# Shortlinks

@webserver.get("/artist/<artist>")
def redirect_artist(artist):
	redirect("/artist?artist=" + artist)
@webserver.get("/track/<artists:path>/<title>")
def redirect_track(artists,title):
	redirect("/track?title=" + title + "&" + "&".join("artist=" + artist for artist in artists.split("/")))

#set graceful shutdown
signal.signal(signal.SIGINT, graceful_exit)
signal.signal(signal.SIGTERM, graceful_exit)

#rename process, this is now required for the daemon manager to work
setproctitle.setproctitle("Maloja")

## start database
database.start_db()
database.dbserver.mount(server=webserver)

log("Starting up Maloja server...")
run(webserver, host=HOST, port=MAIN_PORT, server='waitress')
