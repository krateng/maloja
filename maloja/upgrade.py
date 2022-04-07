# This module should take care of recognizing old install data and upgrading it before the actual server deals with it

import os
import re

from doreah.logging import log
from doreah.io import col

from .globalconf import data_dir, dir_settings
from . import apis


def upgrade_apikeys():

	oldfile = os.path.join(dir_settings['config'],"clients","authenticated_machines.tsv")
	if os.path.exists(oldfile):
		try:
			from doreah import tsv
			clients = tsv.parse(oldfile,"string","string")
			for key,identifier in clients:
				apis.apikeystore[identifier] = key
			os.remove(oldfile)
		except:
			pass


def upgrade_db(callback_add_scrobbles):

	oldfolder = os.path.join(dir_settings['state'],"scrobbles")
	newfolder = os.path.join(dir_settings['state'],".oldscrobbles")
	os.makedirs(newfolder,exist_ok=True)
	if os.path.exists(oldfolder):
		scrobblefiles = [f for f in os.listdir(oldfolder) if f.endswith(".tsv")]
		if len(scrobblefiles) > 0:
			print(col['yellow']("Upgrading v2 Database to v3 Database. This could take a while..."))
			idx = 0
			for sf in scrobblefiles:
				idx += 1
				if re.match(r"[0-9]+_[0-9]+\.tsv",sf):
					origin = 'legacy'
				elif sf == "lastfmimport.tsv":
					origin = 'import:lastfm'
				elif sf == "spotifyimport.tsv":
					origin = 'import:spotify'
				else:
					origin = 'unknown'

				from doreah import tsv
				scrobbles = tsv.parse(os.path.join(oldfolder,sf),"int","string","string","string","string",comments=False)
				scrobblelist = []
				print(f"\tImporting from {sf} ({idx}/{len(scrobblefiles)}) - {len(scrobbles)} Scrobbles")
				for scrobble in scrobbles:
					timestamp, artists, title, album, duration = scrobble
					if album in ('-',''): album = None
					if duration in ('-',''): duration = None
					scrobblelist.append({
						"time":int(timestamp),
						"track":{
							"artists":artists.split('␟'),
							"title":title,
							"length":None
						},
						"duration":duration,
						"origin":origin,
						"extra":{
							"album_name":album
							# saving this in the scrobble instead of the track because for now it's not meant
							# to be authorative information, just payload of the scrobble
						}
					})
				callback_add_scrobbles(scrobblelist)
				os.rename(os.path.join(oldfolder,sf),os.path.join(newfolder,sf))
			print(col['yellow']("Done!"))
