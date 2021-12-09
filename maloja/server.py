#!/usr/bin/env python
import os
from .globalconf import data_dir


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
from threading import Thread
import sys
import signal
import os
import setproctitle
import pkg_resources
import math
from css_html_js_minify import html_minify, css_minify
# url handling
import urllib


######
### TECHNICAL SETTINGS
#####


#settings.config(files=["settings/default.ini","settings/settings.ini"])
#settings.update("settings/default.ini","settings/settings.ini")
MAIN_PORT = settings.get_settings("WEB_PORT")
HOST = settings.get_settings("HOST")
THREADS = 24
BaseRequest.MEMFILE_MAX = 15 * 1024 * 1024

STATICFOLDER = pkg_resources.resource_filename(__name__,"web/static")

webserver = Bottle()

#rename process, this is now required for the daemon manager to work
setproctitle.setproctitle("Maloja")


######
### CSS
#####


def generate_css():
	css = ""
	for f in os.listdir(os.path.join(STATICFOLDER,"css")):
		with open(os.path.join(STATICFOLDER,"css",f),"r") as fd:
			css += fd.read()

	css = css_minify(css)
	return css

css = generate_css()



######
### MINIFY
#####

def clean_html(inp):
	if settings.get_settings("DEV_MODE"): return inp
	else: return html_minify(inp)






######
### ERRORS
#####


@webserver.error(400)
@webserver.error(403)
@webserver.error(404)
@webserver.error(405)
@webserver.error(408)
@webserver.error(500)
@webserver.error(503)
@webserver.error(505)
def customerror(error):
	error_code = error.status_code
	error_desc = error.status
	traceback = error.traceback
	body = error.body or ""
	traceback = traceback.strip() if traceback is not None else "No Traceback"
	adminmode = request.cookies.get("adminmode") == "true" and auth.check(request)

	template = jinja_environment.get_template('error.jinja')
	return template.render(
		error_code=error_code,
		error_desc=error_desc,
		traceback=traceback,
		error_full_desc=body,
		adminmode=adminmode,
	)










######
### REGISTERING ENDPOINTS
#####

aliases = {
	"admin": "admin_overview",
	"manual": "admin_manual",
	"setup": "admin_setup",
	"issues": "admin_issues"
}


### API

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




### STATIC

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
		return static_file(pth,root=data_dir['images']())

	type = pth.split(".")[-1]
	small_pth = pth + "-small"
	if os.path.exists(data_dir['images'](small_pth)):
		response = static_file(small_pth,root=data_dir['images']())
	else:
		try:
			from wand.image import Image
			img = Image(filename=data_dir['images'](pth))
			x,y = img.size[0], img.size[1]
			smaller = min(x,y)
			if smaller > 300:
				ratio = 300/smaller
				img.resize(int(ratio*x),int(ratio*y))
				img.save(filename=data_dir['images'](small_pth))
				response = static_file(small_pth,root=data_dir['images']())
			else:
				response = static_file(pth,root=data_dir['images']())
		except:
			response = static_file(pth,root=data_dir['images']())

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
@webserver.route("/media/<name>.<ext>")
def static(name,ext):
	assert ext in ["txt","ico","jpeg","jpg","png","less","js"]
	response = static_file(ext + "/" + name + "." + ext,root=STATICFOLDER)
	response.set_header("Cache-Control", "public, max-age=3600")
	return response



### DYNAMIC

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
	except (ValueError, IndexError) as e:
		abort(404,"This Artist or Track does not exist")

	if settings.get_settings("DEV_MODE"): jinja_environment.cache.clear()

	log("Generated page {name} in {time:.5f}s".format(name=name,time=clock.stop()),module="debug_performance")
	return clean_html(res)

@webserver.route("/<name:re:admin.*>")
@auth.authenticated
def static_html_private(name):
	return static_html(name)

@webserver.route("/<name>")
def static_html_public(name):
	return static_html(name)

@webserver.route("")
@webserver.route("/")
def mainpage():
	return static_html("start")


# Shortlinks

@webserver.get("/artist/<artist>")
def redirect_artist(artist):
	redirect("/artist?artist=" + artist)
@webserver.get("/track/<artists:path>/<title>")
def redirect_track(artists,title):
	redirect("/track?title=" + title + "&" + "&".join("artist=" + artist for artist in artists.split("/")))


######
### SHUTDOWN
#####


def graceful_exit(sig=None,frame=None):
	#urllib.request.urlopen("http://[::1]:" + str(DATABASE_PORT) + "/sync")
	log("Received signal to shutdown")
	try:
		database.sync()
	except Exception as e:
		log("Error while shutting down!",e)
	log("Server shutting down...")
	os._exit(42)

#set graceful shutdown
signal.signal(signal.SIGINT, graceful_exit)
signal.signal(signal.SIGTERM, graceful_exit)





######
### RUNNING THE SERVER
#####


def run_server():
	log("Starting up Maloja server...")

	## start database
	Thread(target=database.start_db).start()


	try:
		#run(webserver, host=HOST, port=MAIN_PORT, server='waitress')
		waitress.serve(webserver, host=HOST, port=MAIN_PORT, threads=THREADS)
	except OSError:
		log("Error. Is another Maloja process already running?")
		raise



run_server()
