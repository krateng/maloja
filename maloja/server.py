# technical
import sys
import signal
import os
from threading import Thread
import setproctitle
import pkg_resources
from css_html_js_minify import html_minify, css_minify


# server stuff
from bottle import Bottle, static_file, request, response, FormsDict, redirect, BaseRequest, abort
import waitress

# doreah toolkit
from doreah.logging import log
from doreah.timing import Clock
from doreah import auth

# rest of the project
from . import database
from .utilities import resolveImage
from .malojauri import uri_to_internal, remove_identical
from .globalconf import malojaconfig, apikeystore, data_dir
from .jinjaenv.context import jinja_environment
from .apis import init_apis




######
### TECHNICAL SETTINGS
#####

PORT = malojaconfig["PORT"]
HOST = malojaconfig["HOST"]
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
	cssstr = ""
	for file in os.listdir(os.path.join(STATICFOLDER,"css")):
		with open(os.path.join(STATICFOLDER,"css",file),"r") as filed:
			cssstr += filed.read()

	for file in os.listdir(data_dir['css']()):
		if file.endswith(".css"):
			with open(os.path.join(data_dir['css'](file)),"r") as filed:
				cssstr += filed.read()

	cssstr = css_minify(cssstr)
	return cssstr

css = generate_css()



######
### MINIFY
#####

def clean_html(inp):
	return inp

	#if malojaconfig["DEV_MODE"]: return inp
	#else: return html_minify(inp)






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

	ext = pth.split(".")[-1]
	small_pth = pth + "-small"
	if os.path.exists(data_dir['images'](small_pth)):
		response = static_file(small_pth,root=data_dir['images']())
	else:
		try:
			from pyvips import Image
			thumb = Image.thumbnail(data_dir['images'](pth),300)
			thumb.webpsave(data_dir['images'](small_pth))
			response = static_file(small_pth,root=data_dir['images']())
		except Exception:
			response = static_file(pth,root=data_dir['images']())

	#response = static_file("images/" + pth,root="")
	response.set_header("Cache-Control", "public, max-age=86400")
	response.set_header("Content-Type", "image/" + ext)
	return response


@webserver.route("/style.css")
def get_css():
	response.content_type = 'text/css'
	global css
	if malojaconfig["DEV_MODE"]: css = generate_css()
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
	keys = remove_identical(FormsDict.decode(request.query))

	adminmode = request.cookies.get("adminmode") == "true" and auth.check(request)

	clock = Clock()
	clock.start()

	loc_context = {
		"adminmode":adminmode,
		"apikey":request.cookies.get("apikey") if adminmode else None,
		"apikeys":apikeystore,
		"_urikeys":keys, #temporary!
	}
	loc_context["filterkeys"], loc_context["limitkeys"], loc_context["delimitkeys"], loc_context["amountkeys"], loc_context["specialkeys"] = uri_to_internal(keys)

	template = jinja_environment.get_template(name + '.jinja')
	try:
		res = template.render(**loc_context)
	except (ValueError, IndexError):
		abort(404,"This Artist or Track does not exist")

	if malojaconfig["DEV_MODE"]: jinja_environment.cache.clear()

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
	sys.exit(0)

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
		waitress.serve(webserver, host=HOST, port=PORT, threads=THREADS)
	except OSError:
		log("Error. Is another Maloja process already running?")
		raise



run_server()
