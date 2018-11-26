from bottle import route, run, template, static_file, request, response
#import os
from importlib.machinery import SourceFileLoader
#from serverutil import log, db_remove, createVideoFile
import _thread
import waitress
import urllib.request
import urllib.parse


MAIN_PORT = 12345
DATABASE_PORT = 12349

#@route("/<pth:path>/<file:re:.*\\.html>")
#@route("/<pth:path>/<file:re:.*\\.css>")
#@route("/<pth:path>/<file:re:.*\\.js>")
#@route("/<pth:path>/<file:re:.*\\.jpg>")
#@route("/<pth:path>/<file:re:.*\\.png>")
#@route("/<pth:path>/<file:re:.*\\.mp4>")
#@route("/<pth:path>/<file:re:.*\\.mkv>")
#@route("/<pth:path>")
def static(pth):
	
	return static_file(pth,root="")


@route("")
@route("/")
def mainpage():
	return static_file("main.html",root="")



# this is the fallback option. If you run this service behind a reverse proxy, it is recommended to rewrite /db/ requests to the port of the db server
# e.g. location /db { rewrite ^/db(.*)$ $1 break; proxy_pass http://yoururl:12349; }

@route("/db/<pth:path>")
def database(pth):
	keys = request.query
	keystring = "?"
	for k in keys:
		keystring += urllib.parse.quote(k) + "=" + urllib.parse.quote(keys[k]) + "&"
	contents = urllib.request.urlopen("http://localhost:" + str(DATABASE_PORT) + "/" + pth + keystring).read()
	response.content_type = "application/json"
	#print("Returning " + "http://localhost:" + str(DATABASE_PORT) + "/" + pth)
	return contents




## other programs to always run with the server
_thread.start_new_thread(SourceFileLoader("database","database.py").load_module().runserver,(DATABASE_PORT,))

run(host='0.0.0.0', port=MAIN_PORT, server='waitress')
