import os, datetime, re
import json, csv

from doreah.io import col, ask, prompt

from ...cleanup import *
from ...pkg_global.conf import data_dir


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

	from ...database.sqldb import add_scrobbles

	result = {
		"CONFIDENT_IMPORT": 0,
		"UNCERTAIN_IMPORT": 0,
		"CONFIDENT_SKIP": 0,
		"UNCERTAIN_SKIP": 0,
		"FAIL": 0
	}

	filename = os.path.basename(inputf)

	if re.match(r".*\.csv",filename):
		typeid,typedesc = "lastfm","Last.fm"
		importfunc = parse_lastfm

	elif re.match(r"Streaming_History_Audio.+\.json",filename):
		typeid,typedesc = "spotify","Spotify"
		importfunc = parse_spotify_lite

	elif re.match(r"endsong_[0-9]+\.json",filename):
		typeid,typedesc = "spotify","Spotify"
		importfunc = parse_spotify

	elif re.match(r"StreamingHistory[0-9]+\.json",filename):
		typeid,typedesc = "spotify","Spotify"
		importfunc = parse_spotify_lite_legacy

	elif re.match(r"maloja_export[_0-9]*\.json",filename):
		typeid,typedesc = "maloja","Maloja"
		importfunc = parse_maloja

	# username_lb-YYYY-MM-DD.json
	elif re.match(r".*_lb-[0-9-]+\.json",filename):
		typeid,typedesc = "listenbrainz","ListenBrainz"
		importfunc = parse_listenbrainz

	elif re.match(r"\.scrobbler\.log",filename):
		typeid,typedesc = "rockbox","Rockbox"
		importfunc = parse_rockbox

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
			while scrobble['scrobble_time'] in timestamps:
				scrobble['scrobble_time'] += 1
			timestamps.add(scrobble['scrobble_time'])

			# clean up
			(scrobble['track_artists'],scrobble['track_title']) = c.fullclean(scrobble['track_artists'],scrobble['track_title'])

			# extra info
			extrainfo = {}

			scrobblebuffer.append({
				"time":scrobble['scrobble_time'],
				 	"track":{
				 		"artists":scrobble['track_artists'],
				 		"title":scrobble['track_title'],
				 		"length":scrobble['track_length'],
						"album":{
							"albumtitle":scrobble.get('album_name') or None,
							"artists":scrobble.get('album_artists') or scrobble['track_artists'] or None
							# TODO: use same heuristics as with parsing to determine album?
						} if scrobble.get('album_name') else None
				 	},
				 	"duration":scrobble['scrobble_duration'],
				 	"origin":"import:" + typeid,
					"extra":extrainfo
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
		warningmsg = col['indianred'](f"{result['UNCERTAIN_SKIP']} Warning{'s' if result['UNCERTAIN_SKIP'] != 1 else ''}!")
		msg += f" ({warningmsg})"
	print(msg)

	if result['FAIL'] > 0:
		print(col['red'](f"{result['FAIL']} Error{'s' if result['FAIL'] != 1 else ''}!"))


	return result

def parse_spotify_lite_legacy(inputf):
	pth = os.path
	# use absolute paths internally for peace of mind. just change representation for console output
	inputf = pth.abspath(inputf)
	inputfolder = pth.dirname(inputf)
	filenames = re.compile(r'StreamingHistory[0-9]+\.json')
	inputfiles = [os.path.join(inputfolder,f) for f in os.listdir(inputfolder) if filenames.match(f)]

	if len(inputfiles) == 0:
		print("No files found!")
		return

	if inputfiles != [inputf]:
		print("Spotify files should all be imported together to identify duplicates across the whole dataset.")
		if not ask("Import " + ", ".join(col['yellow'](pth.basename(i)) for i in inputfiles) + "?",default=True):
			inputfiles = [inputf]
			print("Only importing", col['yellow'](pth.basename(inputf)))

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
					'track_title':title,
					'track_artists': artist,
					'track_length': None,
					'scrobble_time': timestamp,
					'scrobble_duration':played,
					'album_name': None
				},'')
			except Exception as e:
				yield ('FAIL',None,f"{entry} could not be parsed. Scrobble not imported. ({repr(e)})")
				continue

		print()


def parse_spotify_lite(inputf):
	pth = os.path
	# use absolute paths internally for peace of mind. just change representation for console output
	inputf = pth.abspath(inputf)
	inputfolder = pth.dirname(inputf)
	filenames = re.compile(r'Streaming_History_Audio.+\.json')
	inputfiles = [os.path.join(inputfolder,f) for f in os.listdir(inputfolder) if filenames.match(f)]

	if len(inputfiles) == 0:
		print("No files found!")
		return

	if inputfiles != [inputf]:
		print("Spotify files should all be imported together to identify duplicates across the whole dataset.")
		if not ask("Import " + ", ".join(col['yellow'](pth.basename(i)) for i in inputfiles) + "?",default=True):
			inputfiles = [inputf]
			print("Only importing", col['yellow'](pth.basename(inputf)))

	for inputf in inputfiles:

		print("Importing",col['yellow'](inputf),"...")
		with open(inputf,'r') as inputfd:
			data = json.load(inputfd)

		for entry in data:

			try:
				played = int(entry['ms_played'] / 1000)
				timestamp = int(
					datetime.datetime.strptime(entry['ts'],"%Y-%m-%dT%H:%M:%SZ").timestamp()
				)
				artist = entry['master_metadata_album_artist_name'] # hmmm
				title = entry['master_metadata_track_name']
				album = entry['master_metadata_album_album_name']
				albumartist = entry['master_metadata_album_artist_name']

				if None in [title,artist]:
					yield ('CONFIDENT_SKIP',None,f"{entry} has relevant fields set to null, skipping...")
					continue

				if played < 30:
					yield ('CONFIDENT_SKIP',None,f"{entry} is shorter than 30 seconds, skipping...")
					continue

				yield ("CONFIDENT_IMPORT",{
					'track_title':title,
					'track_artists': artist,
					'track_length': None,
					'scrobble_time': timestamp,
					'scrobble_duration':played,
					'album_name': album,
					'album_artist': albumartist
				},'')
			except Exception as e:
				yield ('FAIL',None,f"{entry} could not be parsed. Scrobble not imported. ({repr(e)})")
				continue

		print()

def parse_spotify(inputf):
	pth = os.path
	# use absolute paths internally for peace of mind. just change representation for console output
	inputf = pth.abspath(inputf)
	inputfolder = pth.dirname(inputf)
	filenames = re.compile(r'endsong_[0-9]+\.json')
	inputfiles = [os.path.join(inputfolder,f) for f in os.listdir(inputfolder) if filenames.match(f)]

	if len(inputfiles) == 0:
		print("No files found!")
		return

	if inputfiles != [inputf]:
		print("Spotify files should all be imported together to identify duplicates across the whole dataset.")
		if not ask("Import " + ", ".join(col['yellow'](pth.basename(i)) for i in inputfiles) + "?",default=True):
			inputfiles = [inputf]
			print("Only importing", col['yellow'](pth.basename(inputf)))

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
					'track_title':title,
					'track_artists': artist,
					'track_length': None,
					'album_name': album,
					'scrobble_time': timestamp,
					'scrobble_duration':played
				},msg)
			except Exception as e:
				yield ('FAIL',None,f"{entry} could not be parsed. Scrobble not imported. ({repr(e)})")
				continue

		print()

def parse_lastfm(inputf):

	with open(inputf,'r',newline='') as inputfd:
		reader = csv.reader(inputfd)

		line = 0
		for row in reader:
			line += 1
			try:
				artist,album,title,time = row
			except ValueError:
				yield ('FAIL',None,f"{row} (Line {line}) does not look like a valid entry. Scrobble not imported.")
				continue

			if time == '':
				yield ('FAIL',None,f"{row} (Line {line}) is missing a timestamp.")
				continue

			try:
				yield ('CONFIDENT_IMPORT',{
					'track_title': title,
					'track_artists': artist,
					'track_length': None,
					'album_name': album,
					'scrobble_time': int(datetime.datetime.strptime(
						time + '+0000',
						"%d %b %Y %H:%M%z"
					).timestamp()),
					'scrobble_duration':None
				},'')
			except Exception as e:
				yield ('FAIL',None,f"{row} (Line {line}) could not be parsed. Scrobble not imported. ({repr(e)})")
				continue

def parse_listenbrainz(inputf):

	with open(inputf,'r') as inputfd:
		data = json.load(inputfd)

	for entry in data:

		try:
			track_metadata = entry['track_metadata']
			additional_info = track_metadata.get('additional_info', {})

			yield ("CONFIDENT_IMPORT",{
				'track_title': track_metadata['track_name'],
				'track_artists': additional_info.get('artist_names') or track_metadata['artist_name'],
				'track_length': int(additional_info.get('duration_ms', 0) / 1000) or additional_info.get('duration'),
				'album_name': track_metadata.get('release_name'),
				'scrobble_time': entry['listened_at'],
				'scrobble_duration': None,
			},'')
		except Exception as e:
			yield ('FAIL',None,f"{entry} could not be parsed. Scrobble not imported. ({repr(e)})")
			continue

def parse_rockbox(inputf):
	with open(inputf,'r') as inputfd:
		for line in inputfd.readlines():
			if line == "#TZ/UNKNOWN":
				use_local_time = True
			elif line == "#TZ/UTC":
				use_local_time = False
			line = line.split("#")[0].split("\n")[0]
			if line:
				try:
					artist,album,track,pos,duration,rate,timestamp,track_id, *_ = line.split("\t") + [None]
					if rate == 'L':
						yield ("CONFIDENT_IMPORT",{
							'track_title':track,
							'track_artists':artist,
							'track_length':duration,
							'album_name':album,
							'scrobble_time':timestamp,
							'scrobble_duration': None
						},'')
					else:
						yield ('CONFIDENT_SKIP',None,f"{track} at {timestamp} is marked as skipped.")
				except Exception as e:
					yield ('FAIL',None,f"{line} could not be parsed. Scrobble not imported. ({repr(e)})")
					continue


def parse_maloja(inputf):

	with open(inputf,'r') as inputfd:
		data = json.load(inputfd)

	scrobbles = data['scrobbles']

	for s in scrobbles:
		try:
			yield ('CONFIDENT_IMPORT',{
				'track_title': s['track']['title'],
				'track_artists': s['track']['artists'],
				'track_length': s['track']['length'],
				'album_name': s['track'].get('album',{}).get('albumtitle','') if s['track'].get('album') is not None else '',
				'album_artists': s['track'].get('album',{}).get('artists',None) if s['track'].get('album') is not None else '',
				'scrobble_time': s['time'],
				'scrobble_duration': s['duration']
			},'')
		except Exception as e:
			yield ('FAIL',None,f"{s} could not be parsed. Scrobble not imported. ({repr(e)})")
			continue
