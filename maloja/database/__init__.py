# server
from bottle import request, response, FormsDict

# rest of the project
from ..cleanup import CleanerAgent
from .. import images
from ..malojatime import register_scrobbletime, time_stamps, ranges, alltime
from ..malojauri import uri_to_internal, internal_to_uri, compose_querystring
from ..thirdparty import proxy_scrobble_all
from ..pkg_global.conf import data_dir, malojaconfig
from ..apis import apikeystore
#db
from . import sqldb
from . import cached
from . import dbcache
from . import exceptions

# doreah toolkit
from doreah.logging import log
from doreah.auth import authenticated_api, authenticated_api_with_alternate
import doreah




# technical
import os
import datetime
import sys
import unicodedata
from collections import namedtuple
from threading import Lock
import yaml, json
import math

# url handling
import urllib



dbstatus = {
	"healthy":False,			# we can access the db
	"rebuildinprogress":False,
	"complete":False			# information is complete
}



def waitfordb(func):
	def newfunc(*args,**kwargs):
		if not dbstatus['healthy']: raise exceptions.DatabaseNotBuilt()
		return func(*args,**kwargs)
	return newfunc



ISSUES = {}

cla = CleanerAgent()





## this function accepts a flat dict - all info of the scrobble should be top level key
## but can contain a list as value
## the following keys are valid:
##		scrobble_duration	int
##		scrobble_time		int
## 		track_title			str, mandatory
##		track_artists		list, mandatory
##		track_length		int
##		album_name			str
##		album_artists		list
##
##
##
##
##
##

def incoming_scrobble(rawscrobble,fix=True,client=None,api=None,dbconn=None):

	missing = []
	for necessary_arg in ["track_artists","track_title"]:
		if not necessary_arg in rawscrobble or len(rawscrobble[necessary_arg]) == 0:
			missing.append(necessary_arg)
	if len(missing) > 0:
		log(f"Invalid Scrobble [Client: {client} | API: {api}]: {rawscrobble} ",color='red')
		raise exceptions.MissingScrobbleParameters(missing)


	log(f"Incoming scrobble [Client: {client} | API: {api}]: {rawscrobble}")

	scrobbledict = rawscrobble_to_scrobbledict(rawscrobble, fix, client)

	sqldb.add_scrobble(scrobbledict,dbconn=dbconn)
	proxy_scrobble_all(scrobbledict['track']['artists'],scrobbledict['track']['title'],scrobbledict['time'])

	dbcache.invalidate_caches(scrobbledict['time'])

	#return {"status":"success","scrobble":scrobbledict}
	return scrobbledict


@waitfordb
def reparse_scrobble(timestamp):
	log(f"Reparsing Scrobble {timestamp}")
	scrobble = sqldb.get_scrobble(timestamp=timestamp, include_internal=True)

	if not scrobble or not scrobble['rawscrobble']:
		return False

	newscrobble = rawscrobble_to_scrobbledict(scrobble['rawscrobble'])

	track_id = sqldb.get_track_id(newscrobble['track'])

	# check if id changed
	if sqldb.get_track_id(scrobble['track']) != track_id:
		sqldb.edit_scrobble(timestamp, {'track':newscrobble['track']})
		dbcache.invalidate_entity_cache()
		dbcache.invalidate_caches()
		return sqldb.get_scrobble(timestamp=timestamp)

	return False


def rawscrobble_to_scrobbledict(rawscrobble, fix=True, client=None):
	# raw scrobble to processed info
	scrobbleinfo = {**rawscrobble}
	if fix:
		scrobbleinfo['track_artists'],scrobbleinfo['track_title'] = cla.fullclean(scrobbleinfo['track_artists'],scrobbleinfo['track_title'])
	scrobbleinfo['scrobble_time'] = scrobbleinfo.get('scrobble_time') or int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp())

	# processed info to internal scrobble dict
	scrobbledict = {
		"time":scrobbleinfo.get('scrobble_time'),
		"track":{
			"artists":scrobbleinfo.get('track_artists'),
			"title":scrobbleinfo.get('track_title'),
			"album":{
				"name":scrobbleinfo.get('album_name'),
				"artists":scrobbleinfo.get('album_artists')
			},
			"length":scrobbleinfo.get('track_length')
		},
		"duration":scrobbleinfo.get('scrobble_duration'),
		"origin":f"client:{client}" if client else "generic",
		"extra":{
			k:scrobbleinfo[k] for k in scrobbleinfo if k not in
			['scrobble_time','track_artists','track_title','track_length','scrobble_duration','album_name','album_artists']
		},
		"rawscrobble":rawscrobble
	}

	return scrobbledict


@waitfordb
def remove_scrobble(timestamp):
	log(f"Deleting Scrobble {timestamp}")
	result = sqldb.delete_scrobble(timestamp)
	dbcache.invalidate_caches(timestamp)

	return result

@waitfordb
def edit_artist(id,artistinfo):
	artist = sqldb.get_artist(id)
	log(f"Renaming {artist} to {artistinfo}")
	result = sqldb.edit_artist(id,artistinfo)
	dbcache.invalidate_entity_cache()
	dbcache.invalidate_caches()

	return result

@waitfordb
def edit_track(id,trackinfo):
	track = sqldb.get_track(id)
	log(f"Renaming {track['title']} to {trackinfo['title']}")
	result = sqldb.edit_track(id,trackinfo)
	dbcache.invalidate_entity_cache()
	dbcache.invalidate_caches()

	return result

@waitfordb
def merge_artists(target_id,source_ids):
	sources = [sqldb.get_artist(id) for id in source_ids]
	target = sqldb.get_artist(target_id)
	log(f"Merging {sources} into {target}")
	result = sqldb.merge_artists(target_id,source_ids)
	dbcache.invalidate_entity_cache()
	dbcache.invalidate_caches()

	return result

@waitfordb
def merge_tracks(target_id,source_ids):
	sources = [sqldb.get_track(id) for id in source_ids]
	target = sqldb.get_track(target_id)
	log(f"Merging {sources} into {target}")
	result = sqldb.merge_tracks(target_id,source_ids)
	dbcache.invalidate_entity_cache()
	dbcache.invalidate_caches()

	return result




@waitfordb
def get_scrobbles(dbconn=None,**keys):
	(since,to) = keys.get('timerange').timestamps()
	if 'artist' in keys:
		result = sqldb.get_scrobbles_of_artist(artist=keys['artist'],since=since,to=to,dbconn=dbconn)
	elif 'track' in keys:
		result = sqldb.get_scrobbles_of_track(track=keys['track'],since=since,to=to,dbconn=dbconn)
	else:
		result = sqldb.get_scrobbles(since=since,to=to,dbconn=dbconn)
	#return result[keys['page']*keys['perpage']:(keys['page']+1)*keys['perpage']]
	return list(reversed(result))


@waitfordb
def get_scrobbles_num(dbconn=None,**keys):
	(since,to) = keys.get('timerange').timestamps()
	if 'artist' in keys:
		result = len(sqldb.get_scrobbles_of_artist(artist=keys['artist'],since=since,to=to,resolve_references=False,dbconn=dbconn))
	elif 'track' in keys:
		result = len(sqldb.get_scrobbles_of_track(track=keys['track'],since=since,to=to,resolve_references=False,dbconn=dbconn))
	else:
		result = sqldb.get_scrobbles_num(since=since,to=to,dbconn=dbconn)
	return result



@waitfordb
def get_tracks(dbconn=None,**keys):
	if keys.get('artist') is None:
		result = sqldb.get_tracks(dbconn=dbconn)
	else:
		result = sqldb.get_tracks_of_artist(keys.get('artist'),dbconn=dbconn)
	return result

@waitfordb
def get_artists(dbconn=None):
	return sqldb.get_artists(dbconn=dbconn)


@waitfordb
def get_charts_artists(dbconn=None,**keys):
	(since,to) = keys.get('timerange').timestamps()
	result = sqldb.count_scrobbles_by_artist(since=since,to=to,dbconn=dbconn)
	return result

@waitfordb
def get_charts_tracks(dbconn=None,**keys):
	(since,to) = keys.get('timerange').timestamps()
	if 'artist' in keys:
		result = sqldb.count_scrobbles_by_track_of_artist(since=since,to=to,artist=keys['artist'],dbconn=dbconn)
	else:
		result = sqldb.count_scrobbles_by_track(since=since,to=to,dbconn=dbconn)
	return result

@waitfordb
def get_pulse(dbconn=None,**keys):

	rngs = ranges(**{k:keys[k] for k in keys if k in ["since","to","within","timerange","step","stepn","trail"]})
	results = []
	for rng in rngs:
		res = get_scrobbles_num(timerange=rng,**{k:keys[k] for k in keys if k != 'timerange'},dbconn=dbconn)
		results.append({"range":rng,"scrobbles":res})

	return results

@waitfordb
def get_performance(dbconn=None,**keys):

	rngs = ranges(**{k:keys[k] for k in keys if k in ["since","to","within","timerange","step","stepn","trail"]})
	results = []

	for rng in rngs:
		if "track" in keys:
			track = sqldb.get_track(sqldb.get_track_id(keys['track'],dbconn=dbconn),dbconn=dbconn)
			charts = get_charts_tracks(timerange=rng,dbconn=dbconn)
			rank = None
			for c in charts:
				if c["track"] == track:
					rank = c["rank"]
					break
		elif "artist" in keys:
			artist = sqldb.get_artist(sqldb.get_artist_id(keys['artist'],dbconn=dbconn),dbconn=dbconn)
			# ^this is the most useless line in programming history
			# but I like consistency
			charts = get_charts_artists(timerange=rng,dbconn=dbconn)
			rank = None
			for c in charts:
				if c["artist"] == artist:
					rank = c["rank"]
					break
		else:
			raise exceptions.MissingEntityParameter()
		results.append({"range":rng,"rank":rank})

	return results

@waitfordb
def get_top_artists(dbconn=None,**keys):

	rngs = ranges(**{k:keys[k] for k in keys if k in ["since","to","within","timerange","step","stepn","trail"]})
	results = []

	for rng in rngs:
		try:
			res = get_charts_artists(timerange=rng,dbconn=dbconn)[0]
			results.append({"range":rng,"artist":res["artist"],"scrobbles":res["scrobbles"]})
		except Exception:
			results.append({"range":rng,"artist":None,"scrobbles":0})

	return results


@waitfordb
def get_top_tracks(dbconn=None,**keys):

	rngs = ranges(**{k:keys[k] for k in keys if k in ["since","to","within","timerange","step","stepn","trail"]})
	results = []

	for rng in rngs:
		try:
			res = get_charts_tracks(timerange=rng,dbconn=dbconn)[0]
			results.append({"range":rng,"track":res["track"],"scrobbles":res["scrobbles"]})
		except Exception:
			results.append({"range":rng,"track":None,"scrobbles":0})

	return results

@waitfordb
def artist_info(dbconn=None,**keys):

	artist = keys.get('artist')
	if artist is None: raise exceptions.MissingEntityParameter()

	artist_id = sqldb.get_artist_id(artist,dbconn=dbconn)
	artist = sqldb.get_artist(artist_id,dbconn=dbconn)
	alltimecharts = get_charts_artists(timerange=alltime(),dbconn=dbconn)
	scrobbles = get_scrobbles_num(artist=artist,timerange=alltime(),dbconn=dbconn)
	#we cant take the scrobble number from the charts because that includes all countas scrobbles
	try:
		c = [e for e in alltimecharts if e["artist"] == artist][0]
		others = sqldb.get_associated_artists(artist,dbconn=dbconn)
		position = c["rank"]
		return {
			"artist":artist,
			"scrobbles":scrobbles,
			"position":position,
			"associated":others,
			"medals":{
				"gold": [year for year in cached.medals_artists if artist_id in cached.medals_artists[year]['gold']],
				"silver": [year for year in cached.medals_artists if artist_id in cached.medals_artists[year]['silver']],
				"bronze": [year for year in cached.medals_artists if artist_id in cached.medals_artists[year]['bronze']],
			},
			"topweeks":len([e for e in cached.weekly_topartists if e == artist_id]),
			"id":artist_id
		}
	except Exception:
		# if the artist isnt in the charts, they are not being credited and we
		# need to show information about the credited one
		replaceartist = sqldb.get_credited_artists(artist)[0]
		c = [e for e in alltimecharts if e["artist"] == replaceartist][0]
		position = c["rank"]
		return {
			"artist":artist,
			"replace":replaceartist,
			"scrobbles":scrobbles,
			"position":position,
			"id":artist_id
		}




@waitfordb
def track_info(dbconn=None,**keys):

	track = keys.get('track')
	if track is None: raise exceptions.MissingEntityParameter()

	track_id = sqldb.get_track_id(track,dbconn=dbconn)
	track = sqldb.get_track(track_id,dbconn=dbconn)
	alltimecharts = get_charts_tracks(timerange=alltime(),dbconn=dbconn)
	#scrobbles = get_scrobbles_num(track=track,timerange=alltime())

	c = [e for e in alltimecharts if e["track"] == track][0]
	scrobbles = c["scrobbles"]
	position = c["rank"]
	cert = None
	threshold_gold, threshold_platinum, threshold_diamond = malojaconfig["SCROBBLES_GOLD","SCROBBLES_PLATINUM","SCROBBLES_DIAMOND"]
	if scrobbles >= threshold_diamond: cert = "diamond"
	elif scrobbles >= threshold_platinum: cert = "platinum"
	elif scrobbles >= threshold_gold: cert = "gold"


	return {
		"track":track,
		"scrobbles":scrobbles,
		"position":position,
		"medals":{
			"gold": [year for year in cached.medals_tracks if track_id in cached.medals_tracks[year]['gold']],
			"silver": [year for year in cached.medals_tracks if track_id in cached.medals_tracks[year]['silver']],
			"bronze": [year for year in cached.medals_tracks if track_id in cached.medals_tracks[year]['bronze']],
		},
		"certification":cert,
		"topweeks":len([e for e in cached.weekly_toptracks if e == track_id]),
		"id":track_id
	}



def get_predefined_rulesets(dbconn=None):
	validchars = "-_abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

	rulesets = []

	for f in os.listdir(data_dir['rules']("predefined")):
		if f.endswith(".tsv"):

			rawf = f.replace(".tsv","")
			valid = all(char in validchars for char in rawf)
			if not valid: continue
			if "_" not in rawf: continue

			try:
				with open(data_dir['rules']("predefined",f)) as tsvfile:
					line1 = tsvfile.readline()
					line2 = tsvfile.readline()

					if "# NAME: " in line1:
						name = line1.replace("# NAME: ","")
					else: name = rawf.split("_")[1]
					desc = line2.replace("# DESC: ","") if "# DESC: " in line2 else ""
					author = rawf.split("_")[0]
			except Exception:
				continue

			ruleset = {"file":rawf}
			rulesets.append(ruleset)
			ruleset["active"] = bool(os.path.exists(data_dir['rules'](f)))
			ruleset["name"] = name
			ruleset["author"] = author
			ruleset["desc"] = desc

	return rulesets


####
## Server operation
####



def start_db():
	# Upgrade database
	from .. import upgrade
	upgrade.upgrade_db(sqldb.add_scrobbles)

	# Load temporary tables
	from . import associated
	associated.load_associated_rules()

	dbstatus['healthy'] = True

	# inform time module about begin of scrobbling
	try:
		firstscrobble = sqldb.get_scrobbles()[0]
		register_scrobbletime(firstscrobble['time'])
	except IndexError:
		register_scrobbletime(int(datetime.datetime.now().timestamp()))


	# create cached information
	cached.update_medals()
	cached.update_weekly()

	dbstatus['complete'] = True






# Search for strings
def db_search(query,type=None):
	results = []
	if type=="ARTIST":
		results = sqldb.search_artist(query)
	if type=="TRACK":
		results = sqldb.search_track(query)
	return results
