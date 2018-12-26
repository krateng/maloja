#!/usr/bin/env python

from bottle import Bottle, route, get, post, error, run, template, static_file, request, response, FormsDict
from importlib.machinery import SourceFileLoader
from htmlgenerators import removeIdentical
import _thread
import waitress
import urllib.request
import urllib.parse
from urllib.error import *
import sys
import signal
import os


MAIN_PORT = 42010
DATABASE_PORT = 42011

webserver = Bottle()


@webserver.route("")
@webserver.route("/")
def mainpage():
	return static_file("main.html",root="")


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
		proxyresponse = urllib.request.urlopen("http://localhost:" + str(DATABASE_PORT) + "/" + pth + keystring)
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
		proxyresponse = urllib.request.urlopen("http://localhost:" + str(DATABASE_PORT) + "/" + pth,request.body)
		contents = proxyresponse.read()
		response.status = proxyresponse.getcode()
		response.content_type = "application/json"
		return contents
	except HTTPError as e:
		response.status = e.code
		return
		
	
	
	return

@webserver.route("/exit")
def shutdown():
	graceful_exit()
	
def graceful_exit(sig=None,frame=None):
	urllib.request.urlopen("http://localhost:" + str(DATABASE_PORT) + "/sync")
	print("Server shutting down...")
	sys.exit()


@webserver.route("/info/<pth:re:.*\\.jpeg>")
@webserver.route("/info/<pth:re:.*\\.jpg>")
@webserver.route("/info/<pth:re:.*\\.png>")
def static_image(pth):
	return static_file("info/" + pth,root="")

@webserver.route("/<name:re:.*\\.html>")
@webserver.route("/<name:re:.*\\.js>")
@webserver.route("/<name:re:.*\\.css>")
@webserver.route("/<name:re:.*\\.png>")
@webserver.route("/<name:re:.*\\.jpeg>")
def static(name):	
	return static_file("website/" + name,root="")
	

	
@webserver.route("/<name>")
def static_html(name):

	keys = removeIdentical(FormsDict.decode(request.query))
	
	# If a python file exists, it provides the replacement dict for the html file
	if os.path.exists("website/" + name + ".py"):
		txt_keys = SourceFileLoader(name,"website/" + name + ".py").load_module().replacedict(keys,DATABASE_PORT)
		with open("website/" + name + ".html") as htmlfile:
			html = htmlfile.read()
			for k in txt_keys:
				html = html.replace(k,txt_keys[k])		
			return html
		
		
	# Otherwise, we just serve the html file
	return static_file("website/" + name + ".html",root="")

#set graceful shutdown
signal.signal(signal.SIGINT, graceful_exit)
signal.signal(signal.SIGTERM, graceful_exit)

#rename process, not important
try:
	import setproctitle
	setproctitle.setproctitle("Maloja")
except:
	pass
	
## start database server
_thread.start_new_thread(SourceFileLoader("database","database.py").load_module().runserver,(DATABASE_PORT,))

run(webserver, host='::', port=MAIN_PORT, server='waitress')
