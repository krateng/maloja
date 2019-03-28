#!/usr/bin/env python

# server stuff
from bottle import Bottle, route, get, post, error, run, template, static_file, request, response, FormsDict, redirect, template
import waitress
# rest of the project
import database
from htmlgenerators import removeIdentical
from utilities import *
from htmlgenerators import KeySplit
# doreah toolkit
from doreah import settings
# technical
from importlib.machinery import SourceFileLoader
import _thread
import sys
import signal
import os
import setproctitle
# url handling
import urllib.request
import urllib.parse
from urllib.error import *



settings.config(files=["settings/default.ini","settings/settings.ini"])
#settings.update("settings/default.ini","settings/settings.ini")
MAIN_PORT, DATABASE_PORT = settings.get_settings("WEB_PORT","API_PORT")


webserver = Bottle()


@webserver.route("")
@webserver.route("/")
def mainpage():
	response = static_html("start")
	return response


# this is the fallback option. If you run this service behind a reverse proxy, it is recommended to rewrite /db/ requests to the port of the db server
# e.g. location /db { rewrite ^/db(.*)$ $1 break; proxy_pass http://yoururl:12349; }

@webserver.get("/db/<pth:path>")
def database_get(pth):
	keys = FormsDict.decode(request.query) # The Dal★Shabet handler
	keystring = "?"
	for k in keys:
		keystring += urllib.parse.quote(k) + "=" + urllib.parse.quote(keys[k]) + "&"
	response.set_header("Access-Control-Allow-Origin","*")
	try:
		proxyresponse = urllib.request.urlopen("http://[::1]:" + str(DATABASE_PORT) + "/" + pth + keystring)
		contents = proxyresponse.read()
		response.status = proxyresponse.getcode()
		response.content_type = "application/json"
		return contents
	except HTTPError as e:
		response.status = e.code
		return

@webserver.post("/db/<pth:path>")
def database_post(pth):
	response.set_header("Access-Control-Allow-Origin","*")
	try:
		proxyresponse = urllib.request.urlopen("http://[::1]:" + str(DATABASE_PORT) + "/" + pth,request.body)
		contents = proxyresponse.read()
		response.status = proxyresponse.getcode()
		response.content_type = "application/json"
		return contents
	except HTTPError as e:
		response.status = e.code
		return

	return


def graceful_exit(sig=None,frame=None):
	#urllib.request.urlopen("http://[::1]:" + str(DATABASE_PORT) + "/sync")
	database.sync()
	log("Server shutting down...")
	os._exit(42)


@webserver.route("/image")
def dynamic_image():
	keys = FormsDict.decode(request.query)
	relevant, _, _, _ = KeySplit(keys)
	result = resolveImage(**relevant)
	if result == "": return ""
	redirect(result,301)

@webserver.route("/images/<pth:re:.*\\.jpeg>")
@webserver.route("/images/<pth:re:.*\\.jpg>")
@webserver.route("/images/<pth:re:.*\\.png>")
@webserver.route("/images/<pth:re:.*\\.gif>")
def static_image(pth):
	small_pth = pth.split(".")
	small_pth.insert(-1,"small")
	small_pth = ".".join(small_pth)
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
	response.set_header("Cache-Control", "public, max-age=604800")
	return response

#@webserver.route("/<name:re:.*\\.html>")
@webserver.route("/<name:re:.*\\.js>")
@webserver.route("/<name:re:.*\\.css>")
@webserver.route("/<name:re:.*\\.png>")
@webserver.route("/<name:re:.*\\.jpeg>")
@webserver.route("/<name:re:.*\\.ico>")
def static(name):
	response = static_file("website/" + name,root="")
	response.set_header("Cache-Control", "public, max-age=604800")
	return response

@webserver.route("/<name>")
def static_html(name):
	linkheaders = ["</css/maloja.css>; rel=preload; as=style"]
	keys = removeIdentical(FormsDict.decode(request.query))

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
		txt_keys,resources = SourceFileLoader(name,"website/" + name + ".py").load_module().instructions(keys)

		# add headers for server push
		for resource in resources:
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

#set graceful shutdown
signal.signal(signal.SIGINT, graceful_exit)
signal.signal(signal.SIGTERM, graceful_exit)

#rename process, this is now required for the daemon manager to work
setproctitle.setproctitle("Maloja")

## start database server
#_thread.start_new_thread(SourceFileLoader("database","database.py").load_module().runserver,(DATABASE_PORT,))
_thread.start_new_thread(database.runserver,(DATABASE_PORT,))

log("Starting up Maloja server...")
run(webserver, host='::', port=MAIN_PORT, server='waitress')
