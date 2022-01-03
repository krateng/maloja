# This module should take care of recognizing old install data and upgrading it before the actual server deals with it

import os
import re

from doreah.logging import log

from .globalconf import data_dir, dir_settings, apikeystore


def upgrade_apikeys():

	oldfile = os.path.join(dir_settings['config'],"clients","authenticated_machines.tsv")
	if os.path.exists(oldfile):
		try:
			from doreah import tsv
			clients = tsv.parse(oldfile,"string","string")
			for key,identifier in clients:
				apikeystore[identifier] = key
			os.remove(oldfile)
		except:
			pass


def upgrade_db(callback_add_scrobbles):
	oldfolder = os.path.join(dir_settings['state'],"scrobbles")
	if os.path.exists(oldfolder):
		scrobblefiles = os.listdir(oldfolder)
		for sf in scrobblefiles:
			if sf.endswith(".tsv"):
				log(f"Found old tsv scrobble file: {sf}")
				if re.match(r"[0-9]+_[0-9]+\.tsv",sf):
					origin = 'native'
				elif sf == "lastfmimport.tsv":
					origin = 'lastfm-import'
				else:
					origin = 'unknown'

				from doreah import tsv
				scrobbles = tsv.parse(os.path.join(oldfolder,sf),"int","string","string","string","string",comments=False)
				scrobblelist = []
				for scrobble in scrobbles:
					timestamp, artists, title, album, duration = scrobble
					if album in ('-',''): album = None
					if duration in ('-',''): duration = None
					scrobblelist.append({
						"time":int(timestamp),
						"track":{
							"artists":artists.split('␟'),
							"title":title,
							"album":{
								"name":album,
								"artists":None
							},
							"length":None
						},
						"duration":duration,
						"origin":origin
					})
				callback_add_scrobbles(scrobblelist)
