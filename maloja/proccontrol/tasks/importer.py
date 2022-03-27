import os, datetime, re

import json, csv

from ...cleanup import *
from doreah.io import col, ask
from ...globalconf import data_dir
#from ...utilities import *




c = CleanerAgent()



def import_scrobbles(inputf):

	ext = inputf.split('.')[-1].lower()

	if ext == 'csv':
		type = "Last.fm"
		outputf = data_dir['scrobbles']("lastfmimport.tsv")
		importfunc = parse_lastfm


	elif ext == 'json':
		type = "Spotify"
		outputf = data_dir['scrobbles']("spotifyimport.tsv")
		importfunc = parse_spotify


	print(f"Parsing {col['yellow'](inputf)} as {col['cyan'](type)} export")

	if os.path.exists(outputf):
		overwrite = ask("Already imported data. Overwrite?",default=False)
		if not overwrite: return

	with open(outputf,"w") as outputfd:
		success = 0
		failed = 0
		timestamps = set()

		for scrobble in importfunc(inputf):
			if scrobble is None:
				failed += 1
			else:
				success += 1

				## We prevent double timestamps in the database creation, so we
				## technically don't need them in the files
				## however since the conversion to maloja is a one-time thing,
				## we should take any effort to make the file as good as possible
				while scrobble['timestamp'] in timestamps:
					scrobble['timestamp'] += 1
				timestamps.add(scrobble['timestamp'])

				# Format fields for tsv
				scrobble['timestamp'] = str(scrobble['timestamp'])
				scrobble['duration'] = str(scrobble['duration']) if scrobble['duration'] is not None else '-'
				(artists,scrobble['title']) = c.fullclean(scrobble['artiststr'],scrobble['title'])
				scrobble['artiststr'] = "␟".join(artists)

				outputline = "\t".join([
					scrobble['timestamp'],
					scrobble['artiststr'],
					scrobble['title'],
					scrobble['album'],
					scrobble['duration']
				])
				outputfd.write(outputline + '\n')

				if success % 100 == 0:
					print(f"Imported {success} scrobbles...")

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
					'artiststr': entry['master_metadata_album_artist_name'],
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
					'artiststr': row[0],
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
