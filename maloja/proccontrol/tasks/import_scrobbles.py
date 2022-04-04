import os, datetime, re
import json, csv

from doreah.io import col, ask, prompt

from ...cleanup import *
from ...globalconf import data_dir
from ...database.sqldb import add_scrobbles

c = CleanerAgent()

outputs = {
	"CONFIDENT_IMPORT": lambda msg: None,
	"UNCERTAIN_IMPORT": lambda msg: print(col['orange'](msg)),
	#"CONFIDENT_SKIP": lambda msg: print(col['ffcba4'](msg)),
	"CONFIDENT_SKIP": lambda msg: None,
	"UNCERTAIN_SKIP": lambda msg: print(col['orange'](msg)),
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
		typeid,typedesc = "lastfm","Last.fm"
		importfunc = parse_lastfm

	elif re.match("endsong_[0-9]+\.json",filename):
		typeid,typedesc = "spotify","Spotify"
		importfunc = parse_spotify_full

	elif re.match("StreamingHistory[0-9]+\.json",filename):
		typeid,typedesc = "spotify","Spotify"
		importfunc = parse_spotify_lite

	elif re.match("maloja_export_[0-9]+\.json",filename):
		typeid,typedesc = "maloja","Maloja"
		importfunc = parse_maloja

	else:
		print("File",inputf,"could not be identified as a valid import source.")
		return result


	print(f"Parsing {col['yellow'](inputf)} as {col['cyan'](typedesc)} export")
	print("This could take a while...")

	timestamps = set()
	scrobblebuffer = []

	for status,scrobble,msg in importfunc(inputf):
		result[status] += 1
		outputs[status](msg)
		if status in ['CONFIDENT_IMPORT','UNCERTAIN_IMPORT']:

			# prevent duplicate timestamps
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
				 		"length":None
				 	},
				 	"duration":scrobble['duration'],
				 	"origin":"import:" + typeid,
					"extra":{
						"album":scrobble['album']
						# saving this in the scrobble instead of the track because for now it's not meant
						# to be authorative information, just payload of the scrobble
					}
			})

			if (result['CONFIDENT_IMPORT'] + result['UNCERTAIN_IMPORT']) % 1000 == 0:
				print(f"Imported {result['CONFIDENT_IMPORT'] + result['UNCERTAIN_IMPORT']} scrobbles...")
				add_scrobbles(scrobblebuffer)
				scrobblebuffer = []

	add_scrobbles(scrobblebuffer)

	msg = f"Successfully imported {result['CONFIDENT_IMPORT'] + result['UNCERTAIN_IMPORT']} scrobbles"
	if result['UNCERTAIN_IMPORT'] > 0:
		warningmsg = col['orange'](f"{result['UNCERTAIN_IMPORT']} Warning{'s' if result['UNCERTAIN_IMPORT'] != 1 else ''}!")
		msg += f" ({warningmsg})"
	print(msg)

	msg = f"Skipped {result['CONFIDENT_SKIP'] + result['UNCERTAIN_SKIP']} scrobbles"
	if result['UNCERTAIN_SKIP'] > 0:
		warningmsg = col['orange'](f"{result['UNCERTAIN_SKIP']} Warning{'s' if result['UNCERTAIN_SKIP'] != 1 else ''}!")
		msg += f" ({warningmsg})"
	print(msg)

	if result['FAIL'] > 0:
		print(col['red'](f"{result['FAIL']} Error{'s' if result['FAIL'] != 1 else ''}!"))


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
					'artists': artist,
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
					'artists': artist,
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
					'artists': artist,
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


def parse_maloja(inputf):

	with open(inputf,'r') as inputfd:
		data = json.load(inputfd)

	scrobbles = data['scrobbles']

	for s in scrobbles:
		try:
			yield ('CONFIDENT_IMPORT',{
				'title': s['track']['title'],
				'artists': s['track']['artists'],
				'album': s['track'].get('album',{}).get('name',''),
				'timestamp': s['time'],
				'duration': s['duration']
			},'')
		except Exception as e:
			yield ('FAIL',None,f"{s} could not be parsed. Scrobble not imported. ({repr(e)})")
			continue
