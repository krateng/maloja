from bottle import route, run, template, static_file, request
#import os
from importlib.machinery import SourceFileLoader
#from serverutil import log, db_remove, createVideoFile
import _thread
import waitress


MAIN_PORT = 12345
DATABASE_PORT = 12349

#@route("/<pth:path>/<file:re:.*\\.html>")
#@route("/<pth:path>/<file:re:.*\\.css>")
#@route("/<pth:path>/<file:re:.*\\.js>")
#@route("/<pth:path>/<file:re:.*\\.jpg>")
#@route("/<pth:path>/<file:re:.*\\.png>")
#@route("/<pth:path>/<file:re:.*\\.mp4>")
#@route("/<pth:path>/<file:re:.*\\.mkv>")
@route("/<pth:path>")
def static(pth):
	
	return static_file(pth,root="")


@route("")
@route("/")
def mainpage():
	keys = request.query
	
	return SourceFileLoader("mainpage","mainpage.py").load_module().GET(keys)
	
@route("/xhttp")
def xhttp():
	keys = request.query
	
	return SourceFileLoader("download","download.py").load_module().GET(keys)



## other programs to always run with the server
#_thread.start_new_thread(SourceFileLoader("downloader","downloader.py").load_module().loop,())
_thread.start_new_thread(SourceFileLoader("database","database.py").load_module().runserver,(DATABASE_PORT,))

print("wat")
run(host='0.0.0.0', port=MAIN_PORT, server='waitress')
