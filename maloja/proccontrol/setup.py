import pkg_resources
from distutils import dir_util
from doreah import settings
from doreah.io import col, ask, prompt
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
