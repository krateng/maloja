import os, datetime, re

import json, csv

from ...cleanup import *
from doreah.io import col, ask, prompt
from ...globalconf import data_dir


c = CleanerAgent()


def warn(msg):
	print(col['orange'](msg))
def err(msg):
	print(col['red'](msg))


def import_scrobbles(inputf):

	ext = inputf.split('.')[-1].lower()

	if ext == 'csv':
		type = "Last.fm"
		outputf = data_dir['scrobbles']("lastfmimport.tsv")
		importfunc = parse_lastfm


	elif ext == 'json' or os.path.isdir(inputf):
		type = "Spotify"
		outputf = data_dir['scrobbles']("spotifyimport.tsv")
		importfunc = parse_spotify
		if os.path.isfile(inputf): inputf = os.path.dirname(inputf)


	print(f"Parsing {col['yellow'](inputf)} as {col['cyan'](type)} export")

	if os.path.exists(outputf):
		while True:
			action = prompt(f"Already imported {type} data. [O]verwrite, [A]ppend or [C]ancel?",default='c').lower()[0]
			if action == 'c':
				return 0,0,0
			elif action == 'a':
				mode = 'a'
				break
			elif action == 'o':
				mode = 'w'
				break
			else:
				print("Could not understand response.")

	with open(outputf,mode) as outputfd:
		success = 0
		failed = 0
		warning = 0
		timestamps = set()

		for scrobble in importfunc(inputf):
			if scrobble is None:
				failed += 1
			elif scrobble is False:
				warning += 1
			else:
				success += 1

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

	return success,failed,warning


def parse_spotify(inputf):

	filenames = re.compile(r'endsong_[0-9]+\.json')

	inputfiles = [os.path.join(inputf,f) for f in os.listdir(inputf) if filenames.match(f)]

	if len(inputfiles) == 0:
		print("No files found!")
	elif ask("Importing the following files: " + ", ".join(col['yellow'](i) for i in inputfiles) + ". Confirm?", default=False):

		# we keep timestamps here as well to remove duplicates because spotify's export
		# is messy - this is specific to this import type and should not be mixed with
		# the outer function timestamp check (which is there to fix duplicate timestamps
		# that are assumed to correspond to actually distinct plays)
		timestamps = {}

		for inputf in inputfiles:

			print("Importing",col['yellow'](inputf),"...")
			with open(inputf,'r') as inputfd:
				data = json.load(inputfd)

			for entry in data:

				try:
					sec = int(entry['ms_played'] / 1000)
					timestamp = entry['offline_timestamp']
					artist = entry['master_metadata_album_artist_name']
					title = entry['master_metadata_track_name']
					album = entry['master_metadata_album_album_name']


					if title is None:
						warn(f"{entry} has no title, skipping...")
						yield False
						continue
					if artist is None:
						warn(f"{entry} has no artist, skipping...")
						yield False
						continue
					if sec < 30:
						warn(f"{entry} is shorter than 30 seconds, skipping...")
						yield False
						continue
					if timestamp in timestamps and (artist,title) in timestamps[timestamp]:
						warn(f"{entry} seems to be a duplicate, skipping...")
						yield False
						continue

					timestamps.setdefault(timestamp,[]).append((artist,title))

					yield {
						'title':title,
						'artiststr': artist,
						'album': album,
					#	'timestamp': int(datetime.datetime.strptime(
					#		entry['ts'].replace('Z','+0000',),
					#		"%Y-%m-%dT%H:%M:%S%z"
					#	).timestamp()),
						'timestamp': timestamp,
						'duration':sec
					}
				except Exception as e:
					err(f"{entry} could not be parsed. Scrobble not imported. ({repr(e)})")
					yield None
					continue

			print()

def parse_lastfm(inputf):

	with open(inputf,'r',newline='') as inputfd:
		reader = csv.reader(inputfd)

		for row in reader:
			try:
				artist,album,title,time = row
			except ValueError:
				warn(f"{row} does not look like a valid entry. Scrobble not imported.")
				yield None
				continue

			try:
				yield {
					'title': title,
					'artiststr': artist,
					'album': album,
					'timestamp': int(datetime.datetime.strptime(
						time + '+0000',
						"%d %b %Y %H:%M%z"
					).timestamp()),
					'duration':None
				}
			except Exception as e:
				err(f"{entry} could not be parsed. Scrobble not imported. ({repr(e)})")
				yield None
				continue
