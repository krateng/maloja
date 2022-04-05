import os, datetime, re

import json, csv

from ...cleanup import *
from doreah.io import col, ask, prompt
from ...globalconf import data_dir


c = CleanerAgent()

outputs = {
	"CONFIDENT_IMPORT": lambda msg: None,
	"UNCERTAIN_IMPORT": lambda msg: print(col['orange'](msg)),
	#"CONFIDENT_SKIP": lambda msg: print(col['ffcba4'](msg)),
	"CONFIDENT_SKIP": lambda msg: None,
	"UNCERTAIN_SKIP": lambda msg: print(col['indianred'](msg)),
	"FAIL": lambda msg: print(col['red'](msg)),
}


def import_scrobbles(inputf):

	result = {
		"CONFIDENT_IMPORT": 0,
		"UNCERTAIN_IMPORT": 0,
		"CONFIDENT_SKIP": 0,
		"UNCERTAIN_SKIP": 0,
		"FAIL": 0
	}

	filename = os.path.basename(inputf)

	if re.match(".*\.csv",filename):
		type = "Last.fm"
		outputf = data_dir['scrobbles']("lastfmimport.tsv")
		importfunc = parse_lastfm

	elif re.match("endsong_[0-9]+\.json",filename):
		type = "Spotify"
		outputf = data_dir['scrobbles']("spotifyimport.tsv")
		importfunc = parse_spotify_full

	elif re.match("StreamingHistory[0-9]+\.json",filename):
		type = "Spotify"
		outputf = data_dir['scrobbles']("spotifyimport.tsv")
		importfunc = parse_spotify_lite

	else:
		print("File",inputf,"could not be identified as a valid import source.")
		return result


	print(f"Parsing {col['yellow'](inputf)} as {col['cyan'](type)} export")


	if os.path.exists(outputf):
		while True:
			action = prompt(f"Already imported {type} data. [O]verwrite, [A]ppend or [C]ancel?",default='c').lower()[0]
			if action == 'c':
				return result
			elif action == 'a':
				mode = 'a'
				break
			elif action == 'o':
				mode = 'w'
				break
			else:
				print("Could not understand response.")
	else:
		mode = 'w'


	with open(outputf,mode) as outputfd:

		timestamps = set()

		for status,scrobble,msg in importfunc(inputf):
			result[status] += 1
			outputs[status](msg)
			if status in ['CONFIDENT_IMPORT','UNCERTAIN_IMPORT']:

				while scrobble['timestamp'] in timestamps:
					scrobble['timestamp'] += 1
				timestamps.add(scrobble['timestamp'])

				# Format fields for tsv
				scrobble['timestamp'] = str(scrobble['timestamp'])
				scrobble['duration'] = str(scrobble['duration']) if scrobble['duration'] is not None else '-'
				scrobble['album'] = scrobble['album'] if scrobble['album'] is not None else '-'
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

				if (result['CONFIDENT_IMPORT'] + result['UNCERTAIN_IMPORT']) % 100 == 0:
					print(f"Imported {result['CONFIDENT_IMPORT'] + result['UNCERTAIN_IMPORT']} scrobbles...")

	return result

def parse_spotify_lite(inputf):
	inputfolder = os.path.dirname(inputf)
	filenames = re.compile(r'StreamingHistory[0-9]+\.json')
	inputfiles = [os.path.join(inputfolder,f) for f in os.listdir(inputfolder) if filenames.match(f)]

	if inputfiles != [inputf]:
		print("Spotify files should all be imported together to identify duplicates across the whole dataset.")
		if not ask("Import " + ", ".join(col['yellow'](i) for i in inputfiles) + "?",default=True):
			inputfiles = [inputf]

	for inputf in inputfiles:

		print("Importing",col['yellow'](inputf),"...")
		with open(inputf,'r') as inputfd:
			data = json.load(inputfd)

		for entry in data:

			try:
				played = int(entry['msPlayed'] / 1000)
				timestamp = int(
					datetime.datetime.strptime(entry['endTime'],"%Y-%m-%d %H:%M").timestamp()
				)
				artist = entry['artistName']
				title = entry['trackName']

				if played < 30:
					yield ('CONFIDENT_SKIP',None,f"{entry} is shorter than 30 seconds, skipping...")
					continue

				yield ("CONFIDENT_IMPORT",{
					'title':title,
					'artiststr': artist,
					'timestamp': timestamp,
					'duration':played,
					'album': None
				},'')
			except Exception as e:
				yield ('FAIL',None,f"{entry} could not be parsed. Scrobble not imported. ({repr(e)})")
				continue

		print()


def parse_spotify_full(inputf):

	inputfolder = os.path.dirname(inputf)
	filenames = re.compile(r'endsong_[0-9]+\.json')
	inputfiles = [os.path.join(inputfolder,f) for f in os.listdir(inputfolder) if filenames.match(f)]

	if inputfiles != [inputf]:
		print("Spotify files should all be imported together to identify duplicates across the whole dataset.")
		if not ask("Import " + ", ".join(col['yellow'](i) for i in inputfiles) + "?",default=True):
			inputfiles = [inputf]

	# we keep timestamps here as well to remove duplicates because spotify's export
	# is messy - this is specific to this import type and should not be mixed with
	# the outer function timestamp check (which is there to fix duplicate timestamps
	# that are assumed to correspond to actually distinct plays)
	timestamps = {}
	inaccurate_timestamps = {}

	for inputf in inputfiles:

		print("Importing",col['yellow'](inputf),"...")
		with open(inputf,'r') as inputfd:
			data = json.load(inputfd)

		for entry in data:

			try:
				played = int(entry['ms_played'] / 1000)
				timestamp = int(entry['offline_timestamp'] / 1000)
				artist = entry['master_metadata_album_artist_name']
				title = entry['master_metadata_track_name']
				album = entry['master_metadata_album_album_name']


				if title is None:
					yield ('CONFIDENT_SKIP',None,f"{entry} has no title, skipping...")
					continue
				if artist is None:
					yield ('CONFIDENT_SKIP',None,f"{entry} has no artist, skipping...")
					continue
				if played < 30:
					yield ('CONFIDENT_SKIP',None,f"{entry} is shorter than 30 seconds, skipping...")
					continue

				# if offline_timestamp is a proper number, we treat it as
				# accurate and check duplicates by that exact timestamp
				if timestamp != 0:

					if timestamp in timestamps and (artist,title) in timestamps[timestamp]:
						yield ('CONFIDENT_SKIP',None,f"{entry} seems to be a duplicate, skipping...")
						continue
					else:
						status = 'CONFIDENT_IMPORT'
						msg = ''
						timestamps.setdefault(timestamp,[]).append((artist,title))

				# if it's 0, we use ts instead, but identify duplicates differently
				# (cause the ts is not accurate)
				else:

					timestamp = int(
						datetime.datetime.strptime(entry['ts'].replace('Z','+0000'),"%Y-%m-%dT%H:%M:%S%z").timestamp()
					)


					ts_group = int(timestamp/10)
					relevant_ts_groups = [ts_group-3,ts_group-2,ts_group-1,ts_group,ts_group+1,ts_group+2,ts_group+3]
					similar_scrobbles = [scrob for tsg in relevant_ts_groups for scrob in inaccurate_timestamps.get(tsg,[])]

					scrobble_describe = (timestamp,entry['spotify_track_uri'],entry['ms_played'])
					found_similar = False
					for scr in similar_scrobbles:
						# scrobbles count as duplicate if:
						# - less than 30 seconds apart
						# - exact same track uri
						# - exact same ms_played
						if (abs(scr[0] - timestamp) < 30) and scr[1:] == scrobble_describe[1:]:
							yield ('UNCERTAIN_SKIP',None,f"{entry} might be a duplicate, skipping...")
							found_similar = True
							break
					else:
						# no duplicates, assume proper scrobble but warn
						status = 'UNCERTAIN_IMPORT'
						msg = f"{entry} might have an inaccurate timestamp."
						inaccurate_timestamps.setdefault(ts_group,[]).append(scrobble_describe)

					if found_similar:
						continue


				yield (status,{
					'title':title,
					'artiststr': artist,
					'album': album,
					'timestamp': timestamp,
					'duration':played
				},msg)
			except Exception as e:
				yield ('FAIL',None,f"{entry} could not be parsed. Scrobble not imported. ({repr(e)})")
				continue

		print()

def parse_lastfm(inputf):

	with open(inputf,'r',newline='') as inputfd:
		reader = csv.reader(inputfd)

		for row in reader:
			try:
				artist,album,title,time = row
			except ValueError:
				yield ('FAIL',None,f"{row} does not look like a valid entry. Scrobble not imported.")
				continue

			try:
				yield ('CONFIDENT_IMPORT',{
					'title': title,
					'artiststr': artist,
					'album': album,
					'timestamp': int(datetime.datetime.strptime(
						time + '+0000',
						"%d %b %Y %H:%M%z"
					).timestamp()),
					'duration':None
				},'')
			except Exception as e:
				yield ('FAIL',None,f"{entry} could not be parsed. Scrobble not imported. ({repr(e)})")
				continue
