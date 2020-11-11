#!/usr/bin/env python
import os
from .globalconf import datadir, DATA_DIR


# server stuff
from bottle import Bottle, route, get, post, error, run, template, static_file, request, response, FormsDict, redirect, template, HTTPResponse, BaseRequest, abort
import waitress

# monkey patching
from . import monkey
# rest of the project
from . import database
from . import malojatime
from . import utilities
from . import malojauri
from .utilities import resolveImage
from .malojauri import uri_to_internal, remove_identical, compose_querystring
from . import globalconf
from .jinjaenv.context import jinja_environment
from jinja2.exceptions import TemplateNotFound
# doreah toolkit
from doreah import settings
from doreah.logging import log
from doreah.timing import Clock
from doreah import auth
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
from css_html_js_minify import html_minify
# url handling
import urllib






#settings.config(files=["settings/default.ini","settings/settings.ini"])
#settings.update("settings/default.ini","settings/settings.ini")
MAIN_PORT = settings.get_settings("WEB_PORT")
HOST = settings.get_settings("HOST")
THREADS = 24
BaseRequest.MEMFILE_MAX = 15 * 1024 * 1024

STATICFOLDER = pkg_resources.resource_filename(__name__,"web/static")
DATAFOLDER = DATA_DIR

webserver = Bottle()
auth.authapi.mount(server=webserver)

from .apis import init_apis
init_apis(webserver)

# redirects for backwards compatibility
@webserver.get("/api/s/<pth:path>")
@webserver.post("/api/s/<pth:path>")
def deprecated_api_s(pth):
	redirect("/apis/" + pth + "?" + request.query_string,308)

@webserver.get("/api/<pth:path>")
@webserver.post("/api/<pth:path>")
def deprecated_api(pth):
	redirect("/apis/mlj_1/" + pth + "?" + request.query_string,308)





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


def clean_html(inp):
	if settings.get_settings("DEV_MODE"): return inp
	else: return html_minify(inp)

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
	errorcode = error.status_code
	errordesc = error.status
	traceback = error.traceback
	traceback = traceback.strip() if traceback is not None else "No Traceback"
	adminmode = request.cookies.get("adminmode") == "true" and auth.check(request)

	template = jinja_environment.get_template('error.jinja')
	res = template.render(errorcode=errorcode,errordesc=errordesc,traceback=traceback,adminmode=adminmode)
	return res



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
	relevant, _, _, _, _ = uri_to_internal(keys)
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
	global css
	if settings.get_settings("DEV_MODE"): css = generate_css()
	return css


@webserver.route("/login")
def login():
	return auth.get_login_page()

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


aliases = {
	"admin": "admin_overview",
	"manual": "admin_manual",
	"setup": "admin_setup",
	"issues": "admin_issues"
}




@webserver.route("/<name:re:admin.*>")
@auth.authenticated
def static_html_private(name):
	return static_html(name)

@webserver.route("/<name>")
def static_html_public(name):
	return static_html(name)

def static_html(name):
	if name in aliases: redirect(aliases[name])
	linkheaders = ["</style.css>; rel=preload; as=style"]
	keys = remove_identical(FormsDict.decode(request.query))

	adminmode = request.cookies.get("adminmode") == "true" and auth.check(request)

	clock = Clock()
	clock.start()

	LOCAL_CONTEXT = {
		"adminmode":adminmode,
		"apikey":request.cookies.get("apikey") if adminmode else None,
		"_urikeys":keys, #temporary!
	}
	lc = LOCAL_CONTEXT
	lc["filterkeys"], lc["limitkeys"], lc["delimitkeys"], lc["amountkeys"], lc["specialkeys"] = uri_to_internal(keys)

	template = jinja_environment.get_template(name + '.jinja')
	try:
		res = template.render(**LOCAL_CONTEXT)
	except ValueError as e:
		abort(404,"Entity does not exist")

	if settings.get_settings("DEV_MODE"): jinja_environment.cache.clear()

	log("Generated page {name} in {time:.5f}s".format(name=name,time=clock.stop()),module="debug_performance")
	return clean_html(res)


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

log("Starting up Maloja server...")
#run(webserver, host=HOST, port=MAIN_PORT, server='waitress')
waitress.serve(webserver, host=HOST, port=MAIN_PORT, threads=THREADS)
