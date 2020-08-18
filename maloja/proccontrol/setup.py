import pkg_resources
from distutils import dir_util
from doreah import settings
from doreah.io import col, ask, prompt
from doreah import auth
import os

from ..globalconf import datadir


# EXTERNAL API KEYS
apikeys = {
	"LASTFM_API_KEY":"Last.fm API Key",
	"FANARTTV_API_KEY":"Fanart.tv API Key",
	"SPOTIFY_API_ID":"Spotify Client ID",
	"SPOTIFY_API_SECRET":"Spotify Client Secret"
}



def copy_initial_local_files():
	folder = pkg_resources.resource_filename("maloja","data_files")
	#shutil.copy(folder,DATA_DIR)
	dir_util.copy_tree(folder,datadir(),update=False)

charset = list(range(10)) + list("abcdefghijklmnopqrstuvwxyz") + list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
def randomstring(length=32):
	import random
	key = ""
	for i in range(length):
		key += str(random.choice(charset))
	return key

def setup():

	copy_initial_local_files()
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
			key = randomstring(64)
			print("Your API Key: " + col["yellow"](key))
			with open(datadir("clients/authenticated_machines.tsv"),"w") as keyfile:
				keyfile.write(key + "\t" + "Default Generated Key")
		else:
			pass


	# PASSWORD
	defaultpassword = settings.get_settings("DEFAULT_PASSWORD")
	forcepassword = settings.get_settings("FORCE_PASSWORD")
	# this is mainly meant for docker, supply password via environment variable

	if forcepassword is not None:
		# user has specified to force the pw, nothing else matters
		auth.defaultuser.setpw(forcepassword)
		print("Password has been set.")
	elif auth.defaultuser.checkpw("admin"):
		# if the actual pw is admin, it means we've never set this up properly (eg first start after update)
		if defaultpassword is None:
			# non-docker installation or user didn't set environment variable
			defaultpassword = randomstring(32)
			newpw = prompt("Please set a password for web backend access. Leave this empty to generate a random password.",skip=SKIP,secret=True)
			if newpw is None:
				newpw = defaultpassword
				print("Generated password:",newpw)
			auth.defaultuser.setpw(newpw)
		else:
			# docker installation (or settings file, but don't do that)
			# we still 'ask' the user to set one, but for docker this will be skipped
			newpw = prompt("Please set a password for web backend access. Leave this empty to use the default password.",skip=SKIP,default=defaultpassword,secret=True)
			auth.defaultuser.setpw(newpw)


	if settings.get_settings("NAME") is None:
		name = prompt("Please enter your name. This will be displayed e.g. when comparing your charts to another user. Leave this empty if you would not like to specify a name right now.",default="Generic Maloja User",skip=SKIP)
		settings.update_settings(datadir("settings/settings.ini"),{"NAME":name},create_new=True)

	if settings.get_settings("SEND_STATS") is None:
		answer = ask("I would like to know how many people use Maloja. Would it be okay to send a daily ping to my server (this contains no data that isn't accessible via your web interface already)?",default=True,skip=SKIP)
		if answer:
			settings.update_settings(datadir("settings/settings.ini"),{"SEND_STATS":True,"PUBLIC_URL":None},create_new=True)
		else:
			settings.update_settings(datadir("settings/settings.ini"),{"SEND_STATS":False},create_new=True)
