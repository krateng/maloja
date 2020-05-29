#!/usr/bin/env python
import os
from .globalconf import datadir, DATA_DIR


# server stuff
from bottle import Bottle, route, get, post, error, run, template, static_file, request, response, FormsDict, redirect, template, HTTPResponse, BaseRequest
import waitress
# templating
from jinja2 import Environment, PackageLoader, select_autoescape
# monkey patching
from . import monkey
# rest of the project
from . import database
from . import htmlmodules
from . import htmlgenerators
from . import malojatime
from . import utilities
from .utilities import resolveImage
from .urihandler import uri_to_internal, remove_identical
from . import urihandler
from . import globalconf
# doreah toolkit
from doreah import settings
from doreah.logging import log
from doreah.timing import Clock
from doreah.pyhp import file as pyhpfile
# technical
#from importlib.machinery import SourceFileLoader
import importlib
import _thread
import sys
import signal
import os
import setproctitle
import pkg_resources
import math
# url handling
import urllib






#settings.config(files=["settings/default.ini","settings/settings.ini"])
#settings.update("settings/default.ini","settings/settings.ini")
MAIN_PORT = settings.get_settings("WEB_PORT")
HOST = settings.get_settings("HOST")
THREADS = 12
BaseRequest.MEMFILE_MAX = 15 * 1024 * 1024

WEBFOLDER = pkg_resources.resource_filename(__name__,"web")
STATICFOLDER = pkg_resources.resource_filename(__name__,"static")
DATAFOLDER = DATA_DIR

webserver = Bottle()

pthjoin = os.path.join

def generate_css():
	import lesscpy
	from io import StringIO
	less = ""
	for f in os.listdir(pthjoin(STATICFOLDER,"less")):
		with open(pthjoin(STATICFOLDER,"less",f),"r") as lessf:
			less += lessf.read()

	css = lesscpy.compile(StringIO(less),minify=True)
	return css

css = generate_css()

#os.makedirs("web/css",exist_ok=True)
#with open("web/css/style.css","w") as f:
#	f.write(css)


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

	if os.path.exists(pthjoin(WEBFOLDER,"errors",str(code) + ".pyhp")):
		return pyhpfile(pthjoin(WEBFOLDER,"errors",str(code) + ".pyhp"),{"errorcode":code})
	else:
		return pyhpfile(pthjoin(WEBFOLDER,"errors","generic.pyhp"),{"errorcode":code})



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
	if globalconf.USE_THUMBOR:
		return static_file(pthjoin("images",pth),root=DATAFOLDER)

	type = pth.split(".")[-1]
	small_pth = pth + "-small"
	if os.path.exists(datadir("images",small_pth)):
		response = static_file(pthjoin("images",small_pth),root=DATAFOLDER)
	else:
		try:
			from wand.image import Image
			img = Image(filename=datadir("images",pth))
			x,y = img.size[0], img.size[1]
			smaller = min(x,y)
			if smaller > 300:
				ratio = 300/smaller
				img.resize(int(ratio*x),int(ratio*y))
				img.save(filename=datadir("images",small_pth))
				response = static_file(pthjoin("images",small_pth),root=DATAFOLDER)
			else:
				response = static_file(pthjoin("images",pth),root=DATAFOLDER)
		except:
			response = static_file(pthjoin("images",pth),root=DATAFOLDER)

	#response = static_file("images/" + pth,root="")
	response.set_header("Cache-Control", "public, max-age=86400")
	response.set_header("Content-Type", "image/" + type)
	return response


@webserver.route("/style.css")
def get_css():
	response.content_type = 'text/css'
	return css


@webserver.route("/<name>.<ext>")
def static(name,ext):
	assert ext in ["txt","ico","jpeg","jpg","png","less","js"]
	response = static_file(ext + "/" + name + "." + ext,root=STATICFOLDER)
	response.set_header("Cache-Control", "public, max-age=3600")
	return response

@webserver.route("/media/<name>.<ext>")
def static(name,ext):
	assert ext in ["ico","jpeg","jpg","png"]
	response = static_file(ext + "/" + name + "." + ext,root=STATICFOLDER)
	response.set_header("Cache-Control", "public, max-age=3600")
	return response






from . import database_packed
dbp = database_packed.DB()

JINJA_CONTEXT = {
	# maloja
	"db": database,
	"dbp":dbp,
	"htmlmodules": htmlmodules,
	"htmlgenerators": htmlgenerators,
	"malojatime": malojatime,
	"utilities": utilities,
	"urihandler": urihandler,
	"settings": settings.get_settings,
	# external
	"urllib": urllib,
	"math":math,
	# config
	"ranges": [
		('day','7 days',malojatime.today().next(-6),'day',7),
		('week','12 weeks',malojatime.thisweek().next(-11),'week',12),
		('month','12 months',malojatime.thismonth().next(-11),'month',12),
		('year','10 years',malojatime.thisyear().next(-9),'year',12)
	],
	"xranges": [
		{"identifier":"day","localisation":"14 days","firstrange":malojatime.today().next(-13),"amount":14},
		{"identifier":"week","localisation":"14 weeks","firstrange":malojatime.thisweek().next(-13),"amount":14},
		{"identifier":"month","localisation":"14 months","firstrange":malojatime.thismonth().next(-13),"amount":14},
		{"identifier":"year","localisation":"14 years","firstrange":malojatime.thisyear().next(-13),"amount":14}
	]
}


jinjaenv = Environment(
	loader=PackageLoader('maloja', 'web/jinja'),
	autoescape=select_autoescape(['html', 'xml'])
)
jinjaenv.globals.update(JINJA_CONTEXT)


@webserver.route("/<name>")
def static_html(name):
	linkheaders = ["</style.css>; rel=preload; as=style"]
	keys = remove_identical(FormsDict.decode(request.query))


	pyhp_file = os.path.exists(pthjoin(WEBFOLDER,"pyhp",name + ".pyhp"))
	html_file = os.path.exists(pthjoin(WEBFOLDER,name + ".html"))
	jinja_file = os.path.exists(pthjoin(WEBFOLDER,"jinja",name + ".jinja"))
	pyhp_pref = settings.get_settings("USE_PYHP")
	jinja_pref = settings.get_settings("USE_JINJA")

	adminmode = request.cookies.get("adminmode") == "true" and database.checkAPIkey(request.cookies.get("apikey")) is not False

	clock = Clock()
	clock.start()

	# if a jinja file exists, use this
	if (jinja_file and jinja_pref) or (jinja_file and not html_file and not pyhp_file):
		LOCAL_CONTEXT = {
			"adminmode":adminmode,
			"apikey":request.cookies.get("apikey") if adminmode else None,
			"_urikeys":keys, #temporary!
		}
		LOCAL_CONTEXT["filterkeys"], LOCAL_CONTEXT["limitkeys"], LOCAL_CONTEXT["delimitkeys"], LOCAL_CONTEXT["amountkeys"] = uri_to_internal(keys)

		template = jinjaenv.get_template(name + '.jinja')

		res = template.render(**LOCAL_CONTEXT)
		log("Generated page {name} in {time:.5f}s (Jinja)".format(name=name,time=clock.stop()),module="debug")
		return res

	# if a pyhp file exists, use this
	elif (pyhp_file and pyhp_pref) or (pyhp_file and not html_file):

		#things we expose to the pyhp pages
		environ = {
			"adminmode":adminmode,
			"apikey":request.cookies.get("apikey") if adminmode else None,
			# maloja
			"db": database,
			"htmlmodules": htmlmodules,
			"htmlgenerators": htmlgenerators,
			"malojatime": malojatime,
			"utilities": utilities,
			"urihandler": urihandler,
			"settings": settings.get_settings,
			# external
			"urllib": urllib
		}
		# request
		environ["filterkeys"], environ["limitkeys"], environ["delimitkeys"], environ["amountkeys"] = uri_to_internal(keys)
		environ["_urikeys"] = keys #temporary!

		#response.set_header("Content-Type","application/xhtml+xml")
		res = pyhpfile(pthjoin(WEBFOLDER,"pyhp",name + ".pyhp"),environ)
		log("Generated page {name} in {time:.5f}s (PYHP)".format(name=name,time=clock.stop()),module="debug")
		return res

	# if not, use the old way
	else:

		with open(pthjoin(WEBFOLDER,name + ".html")) as htmlfile:
			html = htmlfile.read()

		# apply global substitutions
		with open(pthjoin(WEBFOLDER,"common/footer.html")) as footerfile:
			footerhtml = footerfile.read()
		with open(pthjoin(WEBFOLDER,"common/header.html")) as headerfile:
			headerhtml = headerfile.read()
		html = html.replace("</body>",footerhtml + "</body>").replace("</head>",headerhtml + "</head>")


		# If a python file exists, it provides the replacement dict for the html file
		if os.path.exists(pthjoin(WEBFOLDER,name + ".py")):
			#txt_keys = SourceFileLoader(name,"web/" + name + ".py").load_module().replacedict(keys,DATABASE_PORT)
			try:
				module = importlib.import_module(".web." + name,package="maloja")
				txt_keys,resources = module.instructions(keys)
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
		log("Generated page {name} in {time:.5f}s (Python+HTML)".format(name=name,time=clock.stop()),module="debug")
		return html
		#return static_file("web/" + name + ".html",root="")


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
#run(webserver, host=HOST, port=MAIN_PORT, server='waitress')
waitress.serve(webserver, host=HOST, port=MAIN_PORT, threads=THREADS)
