#!/usr/bin/env python3

import subprocess
import sys
import signal
import os
import shutil
from distutils import dir_util
import stat
import pathlib
import pkg_resources
from doreah.control import mainfunction
from doreah.io import col, ask, prompt

from .globalconf import datadir
from .backup import backup




def copy_initial_local_files():
	folder = pkg_resources.resource_filename(__name__,"data_files")
	#shutil.copy(folder,DATA_DIR)
	dir_util.copy_tree(folder,datadir(),update=False)


def setup():

	copy_initial_local_files()

	from doreah import settings

	# EXTERNAL API KEYS
	apikeys = {
		"LASTFM_API_KEY":"Last.fm API Key",
		"FANARTTV_API_KEY":"Fanart.tv API Key",
		"SPOTIFY_API_ID":"Spotify Client ID",
		"SPOTIFY_API_SECRET":"Spotify Client Secret"
	}

	SKIP = settings.get_settings("SKIP_SETUP")

	print("Various external services can be used to display images. If not enough of them are set up, only local images will be used.")
	for k in apikeys:
		key = settings.get_settings(k)
		if key is None:
			print("\t" + "Currently not using a " + apikeys[k] + " for image display.")
		elif key == "ASK":
			print("\t" + "Please enter your " + apikeys[k] + ". If you do not want to use one at this moment, simply leave this empty and press Enter.")
			key = prompt("",types=(str,),default=None,skip=SKIP)
			settings.update_settings(datadir("settings/settings.ini"),{k:key},create_new=True)
		else:
			print("\t" + apikeys[k] + " found.")


	# OWN API KEY
	if os.path.exists(datadir("clients/authenticated_machines.tsv")):
		pass
	else:
		answer = ask("Do you want to set up a key to enable scrobbling? Your scrobble extension needs that key so that only you can scrobble tracks to your database.",default=True,skip=SKIP)
		if answer:
			import random
			key = ""
			for i in range(64):
				key += str(random.choice(list(range(10)) + list("abcdefghijklmnopqrstuvwxyz") + list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")))
			print("Your API Key: " + col["yellow"](key))
			with open(datadir("clients/authenticated_machines.tsv"),"w") as keyfile:
				keyfile.write(key + "\t" + "Default Generated Key")
		else:
			pass


	if settings.get_settings("NAME") is None:
		name = prompt("Please enter your name. This will be displayed e.g. when comparing your charts to another user. Leave this empty if you would not like to specify a name right now.",default="Generic Maloja User",skip=SKIP)
		settings.update_settings(datadir("settings/settings.ini"),{"NAME":name},create_new=True)

	if settings.get_settings("SEND_STATS") is None:
		answer = ask("I would like to know how many people use Maloja. Would it be okay to send a daily ping to my server (this contains no data that isn't accessible via your web interface already)?",default=True,skip=SKIP)
		if answer:
			settings.update_settings(datadir("settings/settings.ini"),{"SEND_STATS":True,"PUBLIC_URL":None},create_new=True)
		else:
			settings.update_settings(datadir("settings/settings.ini"),{"SEND_STATS":False},create_new=True)


def getInstance():
	try:
		output = subprocess.check_output(["pidof","Maloja"])
		pid = int(output)
		return pid
	except:
		return None

def getInstanceSupervisor():
	try:
		output = subprocess.check_output(["pidof","maloja_supervisor"])
		pid = int(output)
		return pid
	except:
		return None

def start():
	setup()
	try:
		#p = subprocess.Popen(["python3","-m","maloja.server"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
		sp = subprocess.Popen(["python3","-m","maloja.supervisor"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
		print(col["green"]("Maloja started!"))

		from doreah import settings
		port = settings.get_settings("WEB_PORT")

		print("Visit your server address (Port " + str(port) + ") to see your web interface. Visit /setup to get started.")
		print("If you're installing this on your local machine, these links should get you there:")
		print("\t" + col["blue"]("http://localhost:" + str(port)))
		print("\t" + col["blue"]("http://localhost:" + str(port) + "/setup"))
		return True
	except:
		print("Error while starting Maloja.")
		return False

def restart():
	wasrunning = stop()
	start()
	return wasrunning

def stop():
	pid_sv = getInstanceSupervisor()
	if pid_sv is not None:
		os.kill(pid_sv,signal.SIGTERM)
#		return True

#	else:
#		print("Server is not running")
#		return False


	pid = getInstance()
	if pid is not None:
#		print("Server is not running")
#		return False
#		pass
#	else:
		os.kill(pid,signal.SIGTERM)
#		print("Maloja stopped! PID: " + str(pid))
	if pid is not None or pid_sv is not None:
		return True
	else:
		return False


def loadlastfm(filename):

	if not os.path.exists(filename):
		print("File could not be found.")
		return

	if os.path.exists(datadir("scrobbles/lastfmimport.tsv")):
		print("Already imported Last.FM data. Overwrite? [y/N]")
		if input().lower() in ["y","yes","yea","1","positive","true"]:
			pass
		else:
			return
	print("Please wait...")
	from .lastfmconverter import convert
	convert(filename,datadir("scrobbles/lastfmimport.tsv"))
	#os.system("python3 -m maloja.lastfmconverter " + filename + " " + datadir("scrobbles/lastfmimport.tsv"))
	print("Successfully imported your Last.FM scrobbles!")

def direct():
	setup()
	from . import server

def backuphere():
	backup(folder=os.getcwd())

def update():
	os.system("pip3 install malojaserver --upgrade --no-cache-dir")
	restart()

def fixdb():
	from .fixexisting import fix
	fix()

@mainfunction({"l":"level"},shield=True)
def main(action,*args,**kwargs):
	actions = {
		"start":restart,
		"restart":restart,
		"stop":stop,
		"import":loadlastfm,
		"debug":direct,
		"backup":backuphere,
		"update":update,
		"fix":fixdb,
		"run":direct
	}
	if action in actions: actions[action](*args,**kwargs)
	else: print("Valid commands: " + " ".join(a for a in actions))

	return True

#if __name__ == "__main__":
#	main()
