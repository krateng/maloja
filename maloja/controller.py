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

from .__init__ import DATA_DIR



def blue(txt): return "\033[94m" + txt + "\033[0m"
def green(txt): return "\033[92m" + txt + "\033[0m"
def yellow(txt): return "\033[93m" + txt + "\033[0m"





origpath = os.getcwd()
os.chdir(DATA_DIR)

def copy_initial_local_files():
	folder = pkg_resources.resource_filename(__name__,"data_files")
	#shutil.copy(folder,DATA_DIR)
	dir_util.copy_tree(folder,DATA_DIR,update=False)


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

	print("Various external services can be used to display images. If not enough of them are set up, only local images will be used.")
	for k in apikeys:
		key = settings.get_settings(k)
		if key is None:
			print("\t" + "Currently not using a " + apikeys[k] + " for image display.")
		elif key == "ASK":
			print("\t" + "Please enter your " + apikeys[k] + ". If you do not want to use one at this moment, simply leave this empty and press Enter.")
			key = input()
			if key == "": key = None
			settings.update_settings("settings/settings.ini",{k:key},create_new=True)
		else:
			print("\t" + apikeys[k] + " found.")


	# OWN API KEY
	if os.path.exists("./clients/authenticated_machines.tsv"):
		pass
	else:
		print("Do you want to set up a key to enable scrobbling? Your scrobble extension needs that key so that only you can scrobble tracks to your database. [Y/n]")
		answer = input()
		if answer.lower() in ["y","yes","yea","1","positive","true",""]:
			import random
			key = ""
			for i in range(64):
				key += str(random.choice(list(range(10)) + list("abcdefghijklmnopqrstuvwxyz") + list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")))
			print("Your API Key: " + yellow(key))
			with open("./clients/authenticated_machines.tsv","w") as keyfile:
				keyfile.write(key + "\t" + "Default Generated Key")
		elif answer.lower() in ["n","no","nay","0","negative","false"]:
			pass


	if settings.get_settings("NAME") is None:
		print("Please enter your name. This will be displayed e.g. when comparing your charts to another user. Leave this empty if you would not like to specify a name right now.")
		name = input()
		if name == "": name = "Generic Maloja User"
		settings.update_settings("settings/settings.ini",{"NAME":name},create_new=True)

	if settings.get_settings("SEND_STATS") is None:
		print("I would like to know how many people use Maloja. Would it be okay to send a daily ping to my server (this contains no data that isn't accessible via your web interface already)? [Y/n]")
		answer = input()
		if answer.lower() in ["y","yes","yea","1","positive","true",""]:
			settings.update_settings("settings/settings.ini",{"SEND_STATS":True},create_new=True)
			settings.update_settings("settings/settings.ini",{"PUBLIC_URL":None},create_new=True)
		else:
			settings.update_settings("settings/settings.ini",{"SEND_STATS":False},create_new=True)


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
		p = subprocess.Popen(["python3","-m","maloja.server"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,cwd=DATA_DIR)
		sp = subprocess.Popen(["python3","-m","maloja.supervisor"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,cwd=DATA_DIR)
		print(green("Maloja started!") + " PID: " + str(p.pid))

		from doreah import settings
		port = settings.get_settings("WEB_PORT")

		print("Visit your server address (Port " + str(port) + ") to see your web interface. Visit /setup to get started.")
		print("If you're installing this on your local machine, these links should get you there:")
		print("\t" + blue("http://localhost:" + str(port)))
		print("\t" + blue("http://localhost:" + str(port) + "/setup"))
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

	pid = getInstance()
	if pid is None:
		print("Server is not running")
		return False
	else:
		os.kill(pid,signal.SIGTERM)
		print("Maloja stopped! PID: " + str(pid))
		return True


def loadlastfm(filename):

	try:
		filename = os.path.join(origpath,filename)
	except:
		print("Please specify a file!")
		return

	if os.path.exists("./scrobbles/lastfmimport.tsv"):
		print("Already imported Last.FM data. Overwrite? [y/N]")
		if input().lower() in ["y","yes","yea","1","positive","true"]:
			pass
		else:
			return
	print("Please wait...")
	os.system("python3 -m maloja.lastfmconverter " + filename + " ./scrobbles/lastfmimport.tsv")
	print("Successfully imported your Last.FM scrobbles!")

def direct():
	from . import server

def backup(level="full",folder=origpath):
	import tarfile
	from datetime import datetime
	import glob



	user_files = {
		"minimal":[
			"rules/*.tsv",
			"scrobbles"
		],
		"full":[
			"clients/authenticated_machines.tsv",
			"images/artists",
			"images/tracks",
			"settings/settings.ini"
		]
	}

	user_files = user_files["minimal"] if level == "minimal" else user_files["minimal"] + user_files["full"]
	real_files = []
	for g in user_files:
		real_files += glob.glob(g)

	now = datetime.utcnow()
	timestr = now.strftime("%Y_%m_%d_%H_%M_%S")
	filename = "maloja_backup_" + timestr + ".tar.gz"
	archivefile = os.path.join(folder,filename)
	assert not os.path.exists(archivefile)
	with tarfile.open(name=archivefile,mode="x:gz") as archive:
		for f in real_files:
			archive.add(f)

def update():
	os.system("pip3 install malojaserver --upgrade --no-cache-dir")

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
		"backup":backup,
		"update":update,
		"fix":fixdb
	}
	if action in actions: actions[action](*args,**kwargs)
	else: print("Valid commands: " + " ".join(a for a in actions))

	return True

#if __name__ == "__main__":
#	main()
