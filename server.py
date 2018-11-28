from bottle import route, run, template, static_file, request, response, FormsDict
from importlib.machinery import SourceFileLoader
import _thread
import waitress
import urllib.request
import urllib.parse
import sys


MAIN_PORT = 12345
DATABASE_PORT = 12349


@route("")
@route("/")
def mainpage():
	return static_file("main.html",root="")



# this is the fallback option. If you run this service behind a reverse proxy, it is recommended to rewrite /db/ requests to the port of the db server
# e.g. location /db { rewrite ^/db(.*)$ $1 break; proxy_pass http://yoururl:12349; }

@route("/db/<pth:path>")
def database(pth):
	keys = FormsDict.decode(request.query) # The Dal★Shabet handler
	for k in keys:
		print(keys[k])
	keystring = "?"
	for k in keys:
		keystring += urllib.parse.quote(k) + "=" + urllib.parse.quote(keys[k]) + "&"
	print(keystring)
	contents = urllib.request.urlopen("http://localhost:" + str(DATABASE_PORT) + "/" + pth + keystring).read()
	response.content_type = "application/json"
	response.set_header("Access-Control-Allow-Origin","*")
	#print("Returning " + "http://localhost:" + str(DATABASE_PORT) + "/" + pth)
	return contents

@route("/exit")
def shutdown():
	urllib.request.urlopen("http://localhost:" + str(DATABASE_PORT) + "/flush")
	print("Server shutting down...")
	sys.exit()


@route("/<pth:path>")
def static(pth):
	
	return static_file(pth,root="")



## start database server
_thread.start_new_thread(SourceFileLoader("database","database.py").load_module().runserver,(DATABASE_PORT,))

run(host='0.0.0.0', port=MAIN_PORT, server='waitress')
