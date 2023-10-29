# This module should take care of recognizing old install data and upgrading it before the actual server deals with it

import os
import re
import csv

from doreah.logging import log
from doreah.io import col

from .pkg_global.conf import data_dir, dir_settings
from .apis import _apikeys


from .database.sqldb import get_maloja_info, set_maloja_info


# Dealing with old style tsv files - these should be phased out everywhere
def read_tsvs(path,types):
	result = []
	for f in os.listdir(path):
		if f.split('.')[-1].lower() != 'tsv': continue
		filepath = os.path.join(path,f)
		result += read_tsv(filepath,types)
	return result

def read_tsv(filename,types):
	with open(filename,'r') as filed:
		reader = csv.reader(filed,delimiter="\t")
		rawentries = [[col for col in entry if col] for entry in reader if len(entry)>0 and not entry[0].startswith('#')]
	converted_entries = [[coltype(col) for col,coltype in zip(entry,types)] for entry in rawentries]
	return converted_entries


def upgrade_apikeys():

	oldfile = os.path.join(dir_settings['config'],"clients","authenticated_machines.tsv")
	if os.path.exists(oldfile):
		try:
				entries = read_tsv(oldfile)
				for key,identifier in entries:
					_apikeys.apikeystore[identifier] = key
				os.remove(oldfile)
		except Exception:
			pass

# v2 to v3 iupgrade
def upgrade_db(callback_add_scrobbles):

	oldfolder = os.path.join(dir_settings['state'],"scrobbles")
	newfolder = os.path.join(dir_settings['state'],".v2scrobbles")
	os.makedirs(newfolder,exist_ok=True)
	if os.path.exists(oldfolder):
		scrobblefiles = [f for f in os.listdir(oldfolder) if f.endswith(".tsv")]
		if len(scrobblefiles) > 0:
			log("Upgrading v2 Database to v3 Database. This could take a while...",color='yellow')
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

				scrobbles = read_tsv(os.path.join(oldfolder,sf),[int,str,str,str,str])
				#scrobbles = tsv.parse(os.path.join(oldfolder,sf),"int","string","string","string","string",comments=False)
				scrobblelist = []
				log(f"\tImporting from {sf} ({idx}/{len(scrobblefiles)}) - {len(scrobbles)} Scrobbles")
				for scrobble in scrobbles:
					timestamp, artists, title, album, duration, *_ = scrobble + [None,None]
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
			log("Done!",color='yellow')


# 3.2 album support
def parse_old_albums():
	setting_name = "db_upgrade_albums"
	if get_maloja_info([setting_name]).get(setting_name):
		pass
	else:
		pass
		#set_maloja_info({setting_name:True})
