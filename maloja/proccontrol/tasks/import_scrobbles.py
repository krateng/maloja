import os, datetime, re

import json, csv

from ...cleanup import *
from doreah.io import col, ask
from ...globalconf import data_dir

from ...database.sqldb import add_scrobbles
#from ...utilities import *




c = CleanerAgent()


# TODO db import
def import_scrobbles(fromfile):

	if not os.path.exists(fromfile):
		print("File could not be found.")
		return

	ext = fromfile.split('.')[-1].lower()

	if ext == 'csv':
		import_type = "Last.fm"
		importfunc = parse_lastfm


	elif ext == 'json':
		import_type = "Spotify"
		importfunc = parse_spotify


	print(f"Parsing {col['yellow'](fromfile)} as {col['cyan'](import_type)} export")

	success = 0
	failed = 0
	timestamps = set()
	scrobblebuffer = []


	for scrobble in importfunc(fromfile):
		if scrobble is None:
			failed += 1
		else:
			success += 1

			# prevent duplicate timestamps within one import file
			while scrobble['timestamp'] in timestamps:
				scrobble['timestamp'] += 1
			timestamps.add(scrobble['timestamp'])
			# clean up
			(scrobble['artists'],scrobble['title']) = c.fullclean(scrobble['artists'],scrobble['title'])

			scrobblebuffer.append({
				"time":scrobble['timestamp'],
				 	"track":{
				 		"artists":scrobble['artists'],
				 		"title":scrobble['title'],
				 		"album":{
				 			"name":scrobble['album'],
				 			"artists":scrobble['artists']
				 		},
				 		"length":None
				 	},
				 	"duration":scrobble['duration'],
				 	"origin":"import:" + import_type,
					"extra":{}
			})

			if success % 1000 == 0:
				print(f"Imported {success} scrobbles...")
				add_scrobbles(scrobblebuffer)
				scrobblebuffer = []

	add_scrobbles(scrobblebuffer)
	print("Successfully imported",success,"scrobbles!")
	if failed > 0:
		print(col['red'](str(failed) + " Errors!"))
	return success,failed


def parse_spotify(inputf):
	with open(inputf,'r') as inputfd:
		data = json.load(inputfd)

	for entry in data:

		sec = int(entry['ms_played'] / 1000)

		if sec > 30:
			try:
				yield {
					'title':entry['master_metadata_track_name'],
					'artists': entry['master_metadata_album_artist_name'],
					'album': entry['master_metadata_album_album_name'],
					'timestamp': int(datetime.datetime.strptime(
						entry['ts'].replace('Z','+0000',),
						"%Y-%m-%dT%H:%M:%S%z"
					).timestamp()),
					'duration':sec
				}
			except:
				print(col['red'](str(entry) + " could not be parsed. Scrobble not imported."))
				yield None
				continue

def parse_lastfm(inputf):

	with open(inputf,'r',newline='') as inputfd:
		reader = csv.reader(inputfd)

		for row in reader:
			try:
				artist,album,title,time = row
			except ValueError:
				print(col['red'](str(row) + " does not look like a valid entry. Scrobble not imported."))
				yield None
				continue

			try:
				yield {
					'title': row[2],
					'artists': row[0],
					'album': row[1],
					'timestamp': int(datetime.datetime.strptime(
						row[3] + '+0000',
						"%d %b %Y %H:%M%z"
					).timestamp()),
					'duration':None
				}
			except:
				print(col['red'](str(row) + " could not be parsed. Scrobble not imported."))
				yield None
				continue
