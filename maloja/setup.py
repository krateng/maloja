import os

from importlib import resources
try:
	from setuptools import distutils
except ImportError:
	import distutils
from doreah.io import col, ask, prompt
from doreah import auth

from .pkg_global.conf import data_dir, dir_settings, malojaconfig



# EXTERNAL API KEYS
ext_apikeys = [
	"LASTFM_API_KEY",
	"SPOTIFY_API_ID",
	"SPOTIFY_API_SECRET",
	"AUDIODB_API_KEY"
]



def copy_initial_local_files():
	with resources.files("maloja") / 'data_files' as folder:
		for cat in dir_settings:
			distutils.dir_util.copy_tree(os.path.join(folder,cat),dir_settings[cat],update=False)

charset = list(range(10)) + list("abcdefghijklmnopqrstuvwxyz") + list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
def randomstring(length=32):
	import random
	return "".join(str(random.choice(charset)) for _ in range(length))

def setup():

	copy_initial_local_files()
	SKIP = malojaconfig["SKIP_SETUP"]

	print("Various external services can be used to display images. If not enough of them are set up, only local images will be used.")
	for k in ext_apikeys:
		keyname = malojaconfig.get_setting_info(k)['name']
		key = malojaconfig[k]
		if key is False:
			print(f"\tCurrently not using a {col['red'](keyname)} for image display.")
		elif key is None or key == "ASK":
			promptmsg = f"\tPlease enter your {col['gold'](keyname)}. If you do not want to use one at this moment, simply leave this empty and press Enter."
			key = prompt(promptmsg,types=(str,),default=False,skip=SKIP)
			malojaconfig[k] = key
		else:
			print(f"\t{col['lawngreen'](keyname)} found.")


	# OWN API KEY
	from .apis import apikeystore
	if len(apikeystore) == 0:
		answer = ask("Do you want to set up a key to enable scrobbling? Your scrobble extension needs that key so that only you can scrobble tracks to your database.",default=True,skip=SKIP)
		if answer:
			key = apikeystore.generate_key('default')
			print("Your API Key: " + col["yellow"](key))

	# PASSWORD
	forcepassword = malojaconfig["FORCE_PASSWORD"]
	# this is mainly meant for docker, supply password via environment variable

	if forcepassword is not None:
		# user has specified to force the pw, nothing else matters
		auth.defaultuser.setpw(forcepassword)
		print("Password has been set.")
	elif auth.defaultuser.checkpw("admin"):
		# if the actual pw is admin, it means we've never set this up properly (eg first start after update)
		while True:
			newpw = prompt("Please set a password for web backend access. Leave this empty to generate a random password.",skip=SKIP,secret=True)
			if newpw is None:
				newpw = randomstring(32)
				print("Generated password:",col["yellow"](newpw))
				break
			else:
				newpw_repeat = prompt("Please type again to confirm.",skip=SKIP,secret=True)
				if newpw != newpw_repeat: print("Passwords do not match!")
				else: break
		auth.defaultuser.setpw(newpw)
