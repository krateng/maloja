# server
from bottle import request, response, FormsDict


# decorator that makes sure this function is only run in normal operation,
# not when we run a task that needs to access the database
def no_aux_mode(func):
	def wrapper(*args,**kwargs):
		from ..pkg_global import conf
		if conf.AUX_MODE: return
		return func(*args,**kwargs)
	return wrapper


# rest of the project
from ..cleanup import CleanerAgent
from .. import images
from ..malojatime import register_scrobbletime, ranges, alltime, today, thisweek, thisyear, MTRangeComposite
from ..malojauri import uri_to_internal, internal_to_uri, compose_querystring
from ..thirdparty import proxy_scrobble_all
from ..pkg_global.conf import data_dir, malojaconfig
from ..apis import apikeystore
#db
from . import sqldb
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

	newfunc.__name__ = func.__name__
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
	albumupdate = (malojaconfig["ALBUM_INFORMATION_TRUST"] == 'last')

	if scrobbledict:

		sqldb.add_scrobble(scrobbledict,update_album=albumupdate,dbconn=dbconn)
		proxy_scrobble_all(scrobbledict['track']['artists'],scrobbledict['track']['title'],scrobbledict['time'])

		dbcache.invalidate_caches(scrobbledict['time'])

		#return {"status":"success","scrobble":scrobbledict}
		return scrobbledict

	else:
		raise exceptions.MissingScrobbleParameters('artist')


@waitfordb
def reparse_scrobble(timestamp):
	log(f"Reparsing Scrobble {timestamp}")
	scrobble = sqldb.get_scrobble(timestamp=timestamp, include_internal=True)

	if not scrobble or not scrobble['rawscrobble']:
		return False

	newscrobble = rawscrobble_to_scrobbledict(scrobble['rawscrobble'])

	if newscrobble:

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
		if scrobbleinfo.get('album_artists'):
			scrobbleinfo['album_artists'] = cla.parseArtists(scrobbleinfo['album_artists'])
		if scrobbleinfo.get("album_title"):
			scrobbleinfo['album_title'] = cla.parseAlbumtitle(scrobbleinfo['album_title'])
	scrobbleinfo['scrobble_time'] = scrobbleinfo.get('scrobble_time') or int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp())

	# if we send [] as albumartists, it means various
	# if we send nothing, the scrobbler just doesnt support it and we assume track artists
	if ('album_title' in scrobbleinfo) and ('album_artists' not in scrobbleinfo):
		scrobbleinfo['album_artists'] = scrobbleinfo.get('track_artists')

	# New plan, do this further down
	# NONE always means there is simply no info, so make a guess or whatever the options say
	# could use the track artists, but probably check if any album with the same name exists first
	# various artists always needs to be specified via []
	# TODO

	# processed info to internal scrobble dict
	scrobbledict = {
		"time":scrobbleinfo.get('scrobble_time'),
		"track":{
			"artists":scrobbleinfo.get('track_artists'),
			"title":scrobbleinfo.get('track_title'),
			"album":{
				"albumtitle":scrobbleinfo.get('album_title'),
				"artists":scrobbleinfo.get('album_artists')
			},
			"length":scrobbleinfo.get('track_length')
		},
		"duration":scrobbleinfo.get('scrobble_duration'),
		"origin":f"client:{client}" if client else "generic",
		"extra":{
			k:scrobbleinfo[k] for k in scrobbleinfo if k not in
			['scrobble_time','track_artists','track_title','track_length','scrobble_duration']#,'album_title','album_artists']
			# we still save album info in extra because the user might select majority album authority
		},
		"rawscrobble":rawscrobble
	}

	if not scrobbledict["track"]["album"]["albumtitle"]:
		del scrobbledict["track"]["album"]

	# discard if invalid
	if len(scrobbledict['track']['artists']) == 0:
		return None
	# TODO: other checks

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
def edit_album(id,albuminfo):
	album = sqldb.get_album(id)
	log(f"Renaming {album['albumtitle']} to {albuminfo['albumtitle']}")
	result = sqldb.edit_album(id,albuminfo)
	dbcache.invalidate_entity_cache()
	dbcache.invalidate_caches()

	return result

@waitfordb
def merge_artists(target_id,source_ids):
	sources = [sqldb.get_artist(id) for id in source_ids]
	target = sqldb.get_artist(target_id)
	log(f"Merging {sources} into {target}")
	sqldb.merge_artists(target_id,source_ids)
	result = {'sources':sources,'target':target}
	dbcache.invalidate_entity_cache()
	dbcache.invalidate_caches()

	return result

@waitfordb
def merge_tracks(target_id,source_ids):
	sources = [sqldb.get_track(id) for id in source_ids]
	target = sqldb.get_track(target_id)
	log(f"Merging {sources} into {target}")
	sqldb.merge_tracks(target_id,source_ids)
	result = {'sources':sources,'target':target}
	dbcache.invalidate_entity_cache()
	dbcache.invalidate_caches()

	return result

@waitfordb
def merge_albums(target_id,source_ids):
	sources = [sqldb.get_album(id) for id in source_ids]
	target = sqldb.get_album(target_id)
	log(f"Merging {sources} into {target}")
	sqldb.merge_albums(target_id,source_ids)
	result = {'sources':sources,'target':target}
	dbcache.invalidate_entity_cache()
	dbcache.invalidate_caches()

	return result



@waitfordb
def associate_albums_to_artist(target_id,source_ids,remove=False):
	sources = [sqldb.get_album(id) for id in source_ids]
	target = sqldb.get_artist(target_id)
	if remove:
		log(f"Removing {sources} from {target}")
		sqldb.remove_artists_from_albums(artist_ids=[target_id],album_ids=source_ids)
	else:
		log(f"Adding {sources} into {target}")
		sqldb.add_artists_to_albums(artist_ids=[target_id],album_ids=source_ids)
	result = {'sources':sources,'target':target}
	dbcache.invalidate_entity_cache()
	dbcache.invalidate_caches()

	return result

@waitfordb
def associate_tracks_to_artist(target_id,source_ids,remove=False):
	sources = [sqldb.get_track(id) for id in source_ids]
	target = sqldb.get_artist(target_id)
	if remove:
		log(f"Removing {sources} from {target}")
		sqldb.remove_artists_from_tracks(artist_ids=[target_id],track_ids=source_ids)
	else:
		log(f"Adding {sources} into {target}")
		sqldb.add_artists_to_tracks(artist_ids=[target_id],track_ids=source_ids)
	result = {'sources':sources,'target':target}
	dbcache.invalidate_entity_cache()
	dbcache.invalidate_caches()

	return result

@waitfordb
def associate_tracks_to_album(target_id,source_ids):
	# target_id None means remove from current album!
	sources = [sqldb.get_track(id) for id in source_ids]
	if target_id:
		target = sqldb.get_album(target_id)
		log(f"Adding {sources} into {target}")
		sqldb.add_tracks_to_albums({src:target_id for src in source_ids})
	else:
		sqldb.remove_album(source_ids)
	result = {'sources':sources,'target':target}
	dbcache.invalidate_entity_cache()
	dbcache.invalidate_caches()

	return result



@waitfordb
def get_scrobbles(dbconn=None,**keys):
	(since,to) = keys.get('timerange').timestamps()

	reverse = keys.get('reverse',True) # comaptibility with old calls
	if keys.get('perpage',math.inf) is not math.inf:
		limit = (keys.get('page',0)+1) * keys.get('perpage',100)
		behead = keys.get('page',0) * keys.get('perpage',100)
	else:
		limit = None
		behead = 0


	associated = keys.get('associated',False)
	if 'artist' in keys:
		result = sqldb.get_scrobbles_of_artist(artist=keys['artist'],since=since,to=to,associated=associated,limit=limit,reverse=reverse,dbconn=dbconn)
	elif 'track' in keys:
		result = sqldb.get_scrobbles_of_track(track=keys['track'],since=since,to=to,limit=limit,reverse=reverse,dbconn=dbconn)
	elif 'album' in keys:
		result = sqldb.get_scrobbles_of_album(album=keys['album'],since=since,to=to,limit=limit,reverse=reverse,dbconn=dbconn)
	else:
		result = sqldb.get_scrobbles(since=since,to=to,limit=limit,reverse=reverse,dbconn=dbconn)
	#return result[keys['page']*keys['perpage']:(keys['page']+1)*keys['perpage']]

	#print(result)

	return list(result[behead:])


@waitfordb
def get_scrobbles_num(dbconn=None,**keys):
	(since,to) = keys.get('timerange').timestamps()
	associated = keys.get('associated',False)
	if 'artist' in keys:
		result = len(sqldb.get_scrobbles_of_artist(artist=keys['artist'],since=since,to=to,associated=associated,resolve_references=False,dbconn=dbconn))
	elif 'track' in keys:
		result = len(sqldb.get_scrobbles_of_track(track=keys['track'],since=since,to=to,resolve_references=False,dbconn=dbconn))
	elif 'album' in keys:
		result = len(sqldb.get_scrobbles_of_album(album=keys['album'],since=since,to=to,resolve_references=False,dbconn=dbconn))
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
def get_albums(dbconn=None,**keys):
	if keys.get('artist') is None:
		result = sqldb.get_albums(dbconn=dbconn)
	else:
		result = sqldb.get_albums_of_artists([sqldb.get_artist_id(keys.get('artist'),create_new=False)],dbconn=dbconn)
	return result

@waitfordb
def get_artists(dbconn=None):
	return sqldb.get_artists(dbconn=dbconn)

@waitfordb
def get_albums_artist_appears_on(dbconn=None,**keys):

	artist_id = sqldb.get_artist_id(keys['artist'],dbconn=dbconn)

	albums = sqldb.get_albums_artists_appear_on([artist_id],dbconn=dbconn).get(artist_id) or []
	ownalbums = sqldb.get_albums_of_artists([artist_id],dbconn=dbconn).get(artist_id) or []

	result = {
		"own_albums":ownalbums,
		"appears_on":[a for a in albums if a not in ownalbums]
	}

	return result

@waitfordb
def get_tracks_without_album(dbconn=None,resolve_ids=True):
	return get_charts_tracks(album=None,timerange=alltime(),resolve_ids=resolve_ids,dbconn=dbconn)

@waitfordb
def get_charts_artists(dbconn=None,resolve_ids=True,**keys):
	(since,to) = keys.get('timerange').timestamps()
	separate = keys.get('separate',False)
	result = sqldb.count_scrobbles_by_artist(since=since,to=to,resolve_ids=resolve_ids,associated=(not separate),dbconn=dbconn)

	if resolve_ids:
		# only add associated info if we resolve
		map = sqldb.get_associated_artist_map(artist_ids=[entry['artist_id'] for entry in result if 'artist_id' in entry])
		for entry in result:
			if "artist_id" in entry:
				entry['associated_artists'] = map[entry['artist_id']]
	return result

@waitfordb
def get_charts_tracks(dbconn=None,resolve_ids=True,**keys):
	(since,to) = keys.get('timerange').timestamps()
	if 'artist' in keys:
		result = sqldb.count_scrobbles_by_track_of_artist(since=since,to=to,artist=keys['artist'],associated=keys.get('associated',False),resolve_ids=resolve_ids,dbconn=dbconn)
	elif 'album' in keys:
		result = sqldb.count_scrobbles_by_track_of_album(since=since,to=to,album=keys['album'],resolve_ids=resolve_ids,dbconn=dbconn)
	else:
		result = sqldb.count_scrobbles_by_track(since=since,to=to,resolve_ids=resolve_ids,dbconn=dbconn)
	return result

@waitfordb
def get_charts_albums(dbconn=None,resolve_ids=True,only_own_albums=False,**keys):
	# TODO: different scrobble numbers for only own tracks on own album etc?
	(since,to) = keys.get('timerange').timestamps()

	if 'artist' in keys:
		result = sqldb.count_scrobbles_by_album_combined(since=since,to=to,artist=keys['artist'],associated=keys.get('associated',False),resolve_ids=resolve_ids,dbconn=dbconn)
		if only_own_albums:
			# TODO: this doesnt take associated into account and doesnt change ranks
			result = [e for e in result if keys['artist'] in (e['album']['artists'] or [])]
	else:
		result = sqldb.count_scrobbles_by_album(since=since,to=to,resolve_ids=resolve_ids,dbconn=dbconn)
	return result

@waitfordb
def get_pulse(dbconn=None,**keys):

	# amountkeys for pulse and performance aren't really necessary
	# since the amount of entries is completely determined by the time keys
	# but lets just include it in case
	reverse = keys.get('reverse',False)
	if keys.get('perpage',math.inf) is not math.inf:
		limit = (keys.get('page',0)+1) * keys.get('perpage',100)
		behead = keys.get('page',0) * keys.get('perpage',100)
	else:
		limit = math.inf
		behead = 0

	rngs = ranges(**{k:keys[k] for k in keys if k in ["since","to","within","timerange","step","stepn","trail"]})
	if reverse: rngs = reversed(list(rngs))
	results = []
	for rng in rngs:

		# count down how many we need
		if limit==0:
			break
		limit -= 1

		# skip prev pages
		if behead>0:
			behead -= 1
			continue

		res = get_scrobbles_num(timerange=rng,**{k:keys[k] for k in keys if k != 'timerange'},dbconn=dbconn)
		if keys.get('artist') and keys.get('associated',False):
			res_real = get_scrobbles_num(timerange=rng,**{k:keys[k] for k in keys if k not in ['timerange','associated']},associated=False,dbconn=dbconn)
			# this isnt really efficient, we could do that in one db call, but i dont wanna reorganize rn
		else:
			res_real = res
		results.append({"range":rng,"scrobbles":res,"real_scrobbles":res_real})

	return results

@waitfordb
def get_performance(dbconn=None,**keys):

	# amountkeys for pulse and performance aren't really necessary
	# since the amount of entries is completely determined by the time keys
	# but lets just include it in case
	reverse = keys.get('reverse',False)
	if keys.get('perpage',math.inf) is not math.inf:
		limit = (keys.get('page',0)+1) * keys.get('perpage',100)
		behead = keys.get('page',0) * keys.get('perpage',100)
	else:
		limit = math.inf
		behead = 0

	separate = keys.get('separate')

	rngs = ranges(**{k:keys[k] for k in keys if k in ["since","to","within","timerange","step","stepn","trail"]})
	if reverse: rngs = reversed(list(rngs))
	results = []

	for rng in rngs:

		# count down how many we need
		if limit==0:
			break
		limit -= 1

		# skip prev pages
		if behead>0:
			behead -= 1
			continue






		if "track" in keys:
			track_id = sqldb.get_track_id(keys['track'],create_new=False,dbconn=dbconn)
			if not track_id:
				raise exceptions.TrackDoesNotExist(keys['track'])
			#track = sqldb.get_track(track_id,dbconn=dbconn)
			charts = get_charts_tracks(timerange=rng,resolve_ids=False,dbconn=dbconn)
			rank = None
			for c in charts:
				if c["track_id"] == track_id:
					rank = c["rank"]
					break
		elif "artist" in keys:
			artist_id = sqldb.get_artist_id(keys['artist'],create_new=False,dbconn=dbconn)
			if not artist_id:
				raise exceptions.ArtistDoesNotExist(keys['artist'])
			#artist = sqldb.get_artist(artist_id,dbconn=dbconn)
			# ^this is the most useless line in programming history
			# but I like consistency
			charts = get_charts_artists(timerange=rng,resolve_ids=False,separate=separate,dbconn=dbconn)
			rank = None
			for c in charts:
				if c["artist_id"] == artist_id:
					rank = c["rank"]
					break
		elif "album" in keys:
			album_id = sqldb.get_album_id(keys['album'],create_new=False,dbconn=dbconn)
			if not album_id:
				raise exceptions.AlbumDoesNotExist(keys['album'])
			#album = sqldb.get_album(album_id,dbconn=dbconn)
			charts = get_charts_albums(timerange=rng,resolve_ids=False,dbconn=dbconn)
			rank = None
			for c in charts:
				if c["album_id"] == album_id:
					rank = c["rank"]
					break
		else:
			raise exceptions.MissingEntityParameter()
		results.append({"range":rng,"rank":rank})

	return results

@waitfordb
def get_top_artists(dbconn=None,**keys):

	separate = keys.get('separate')

	rngs = ranges(**{k:keys[k] for k in keys if k in ["since","to","within","timerange","step","stepn","trail"]})
	results = []

	for rng in rngs:
		try:
			res = get_charts_artists(timerange=rng,separate=separate,dbconn=dbconn)[0]
			results.append({"range":rng,"artist":res["artist"],"scrobbles":res["scrobbles"],"real_scrobbles":res["real_scrobbles"],"associated_artists":sqldb.get_associated_artists(res["artist"])})
		except Exception:
			results.append({"range":rng,"artist":None,"scrobbles":0,"real_scrobbles":0})

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
def get_top_albums(dbconn=None,**keys):

	rngs = ranges(**{k:keys[k] for k in keys if k in ["since","to","within","timerange","step","stepn","trail"]})
	results = []

	for rng in rngs:
		try:
			res = get_charts_albums(timerange=rng,dbconn=dbconn)[0]
			results.append({"range":rng,"album":res["album"],"scrobbles":res["scrobbles"]})
		except Exception:
			results.append({"range":rng,"album":None,"scrobbles":0})

	return results

@waitfordb
def artist_info(dbconn=None,**keys):

	artist = keys.get('artist')
	if artist is None: raise exceptions.MissingEntityParameter()

	artist_id = sqldb.get_artist_id(artist,create_new=False,dbconn=dbconn)
	if not artist_id: raise exceptions.ArtistDoesNotExist(artist)

	artist = sqldb.get_artist(artist_id,dbconn=dbconn)
	alltimecharts = get_charts_artists(timerange=alltime(),dbconn=dbconn)
	#we cant take the scrobble number from the charts because that includes all countas scrobbles
	scrobbles = get_scrobbles_num(artist=artist,timerange=alltime(),dbconn=dbconn)
	albums = sqldb.get_albums_of_artists(set([artist_id]),dbconn=dbconn)
	isalbumartist = len(albums.get(artist_id,[]))>0

	cert = None
	own_track_charts = get_charts_tracks(timerange=alltime(),resolve_ids=False,artist=artist,dbconn=dbconn)
	own_album_charts = get_charts_albums(timerange=alltime(),resolve_ids=True,artist=artist,dbconn=dbconn)
	# we resolve ids here which we don't need to. however, on the jinja page we make that same call
	# later again with resolve ids, so its a cache miss and it doubles page load time
	# TODO: find better solution
	if own_track_charts:
		c = own_track_charts[0]
		tscrobbles = c["scrobbles"]
		threshold_gold, threshold_platinum, threshold_diamond = malojaconfig["SCROBBLES_GOLD","SCROBBLES_PLATINUM","SCROBBLES_DIAMOND"]
		if tscrobbles >= threshold_diamond: cert = "diamond"
		elif tscrobbles >= threshold_platinum: cert = "platinum"
		elif tscrobbles >= threshold_gold: cert = "gold"
	if own_album_charts:
		c = own_album_charts[0]
		ascrobbles = c["scrobbles"]
		threshold_gold, threshold_platinum, threshold_diamond = malojaconfig["SCROBBLES_GOLD_ALBUM","SCROBBLES_PLATINUM_ALBUM","SCROBBLES_DIAMOND_ALBUM"]
		if ascrobbles >= threshold_diamond: cert = "diamond"
		elif ascrobbles >= threshold_platinum and cert != "diamond": cert = "platinum"
		elif ascrobbles >= threshold_gold and not cert: cert = "gold"

	twk = thisweek()
	tyr = thisyear()

	# base info for everyone
	result = {
		"artist":artist,
		"scrobbles":scrobbles,
		"id":artist_id,
		"isalbumartist":isalbumartist,
		"certification":cert,
	}

	# check if credited to someone else
	parent_artists = sqldb.get_credited_artists(artist)
	if len(parent_artists) == 0:
		c = [e for e in alltimecharts if e["artist"] == artist]
		position = c[0]["rank"] if len(c) > 0 else None
		others = sqldb.get_associated_artists(artist,dbconn=dbconn)
		result.update({
			"position":position,
			"associated":others,
			"medals":{
				"gold": [year.desc() for year in ranges(step='year') if (year != tyr) and any(
					(e.get('artist_id') == artist_id) and (e.get('rank') == 1) for e in
					sqldb.count_scrobbles_by_artist(since=year.first_stamp(),to=year.last_stamp(),resolve_ids=False,dbconn=dbconn)
				)],
				"silver": [year.desc() for year in ranges(step='year') if (year != tyr) and any(
					(e.get('artist_id') == artist_id) and (e.get('rank') == 2) for e in
					sqldb.count_scrobbles_by_artist(since=year.first_stamp(),to=year.last_stamp(),resolve_ids=False,dbconn=dbconn)
				)],
				"bronze": [year.desc() for year in ranges(step='year') if (year != tyr) and any(
					(e.get('artist_id') == artist_id) and (e.get('rank') == 3) for e in
					sqldb.count_scrobbles_by_artist(since=year.first_stamp(),to=year.last_stamp(),resolve_ids=False,dbconn=dbconn)
				)]
			},
			"topweeks":len([
				week for week in ranges(step="week") if (week != twk) and any(
					(e.get('artist_id') == artist_id) and (e.get('rank') == 1) for e in
					sqldb.count_scrobbles_by_artist(since=week.first_stamp(),to=week.last_stamp(),resolve_ids=False,associated=True,dbconn=dbconn)
				)
				# we don't need to check the whole thing, just until rank is lower, but... well, its a list comprehension
			])
		})

	else:
		replaceartist = parent_artists[0]
		c = [e for e in alltimecharts if e["artist"] == replaceartist][0]
		position = c["rank"]
		result.update({
			"replace":replaceartist,
			"position":position
		})

	return result



@waitfordb
def track_info(dbconn=None,**keys):

	track = keys.get('track')
	if track is None: raise exceptions.MissingEntityParameter()

	track_id = sqldb.get_track_id(track,create_new=False,dbconn=dbconn)
	if not track_id: raise exceptions.TrackDoesNotExist(track)

	track = sqldb.get_track(track_id,dbconn=dbconn)
	alltimecharts = get_charts_tracks(timerange=alltime(),resolve_ids=False,dbconn=dbconn)
	#scrobbles = get_scrobbles_num(track=track,timerange=alltime())

	c = [e for e in alltimecharts if e["track_id"] == track_id][0]
	scrobbles = c["scrobbles"]
	position = c["rank"]
	cert = None
	threshold_gold, threshold_platinum, threshold_diamond = malojaconfig["SCROBBLES_GOLD","SCROBBLES_PLATINUM","SCROBBLES_DIAMOND"]
	if scrobbles >= threshold_diamond: cert = "diamond"
	elif scrobbles >= threshold_platinum: cert = "platinum"
	elif scrobbles >= threshold_gold: cert = "gold"

	twk = thisweek()
	tyr = thisyear()

	return {
		"track":track,
		"scrobbles":scrobbles,
		"position":position,
		"medals":{
			"gold": [year.desc() for year in ranges(step='year') if (year != tyr) and any(
				(e.get('track_id') == track_id) and (e.get('rank') == 1) for e in
				sqldb.count_scrobbles_by_track(since=year.first_stamp(),to=year.last_stamp(),resolve_ids=False,dbconn=dbconn)
			)],
			"silver": [year.desc() for year in ranges(step='year') if (year != tyr) and any(
				(e.get('track_id') == track_id) and (e.get('rank') == 2) for e in
				sqldb.count_scrobbles_by_track(since=year.first_stamp(),to=year.last_stamp(),resolve_ids=False,dbconn=dbconn)
			)],
			"bronze": [year.desc() for year in ranges(step='year') if (year != tyr) and any(
				(e.get('track_id') == track_id) and (e.get('rank') == 3) for e in
				sqldb.count_scrobbles_by_track(since=year.first_stamp(),to=year.last_stamp(),resolve_ids=False,dbconn=dbconn)
			)]
		},
		"certification":cert,
		"topweeks":len([
			week for week in ranges(step="week") if (week != twk) and any(
				(e.get('track_id') == track_id) and (e.get('rank') == 1) for e in
				sqldb.count_scrobbles_by_track(since=week.first_stamp(),to=week.last_stamp(),resolve_ids=False,dbconn=dbconn)
			)
		]),
		"id":track_id
	}


@waitfordb
def album_info(dbconn=None,reduced=False,**keys):

	album = keys.get('album')
	if album is None: raise exceptions.MissingEntityParameter()

	album_id = sqldb.get_album_id(album,create_new=False,dbconn=dbconn)
	if not album_id: raise exceptions.AlbumDoesNotExist(album)

	album = sqldb.get_album(album_id,dbconn=dbconn)

	extrainfo = {}

	if reduced:
		scrobbles = get_scrobbles_num(album=album,timerange=alltime())
	else:
		alltimecharts = get_charts_albums(timerange=alltime(),dbconn=dbconn)
		c = [e for e in alltimecharts if e["album"] == album][0]
		scrobbles = c["scrobbles"]
		position = c["rank"]
		extrainfo['position'] = position

	cert = None
	threshold_gold, threshold_platinum, threshold_diamond = malojaconfig["SCROBBLES_GOLD_ALBUM","SCROBBLES_PLATINUM_ALBUM","SCROBBLES_DIAMOND_ALBUM"]
	if scrobbles >= threshold_diamond: cert = "diamond"
	elif scrobbles >= threshold_platinum: cert = "platinum"
	elif scrobbles >= threshold_gold: cert = "gold"

	if reduced:
		pass
	else:
		twk = thisweek()
		tyr = thisyear()
		extrainfo.update({
			"medals":{
				"gold": [year.desc() for year in ranges(step='year') if (year != tyr) and any(
					(e.get('album_id') == album_id) and (e.get('rank') == 1) for e in
					sqldb.count_scrobbles_by_album(since=year.first_stamp(),to=year.last_stamp(),resolve_ids=False,dbconn=dbconn)
				)],
				"silver": [year.desc() for year in ranges(step='year') if (year != tyr) and any(
					(e.get('album_id') == album_id) and (e.get('rank') == 2) for e in
					sqldb.count_scrobbles_by_album(since=year.first_stamp(),to=year.last_stamp(),resolve_ids=False,dbconn=dbconn)
				)],
				"bronze": [year.desc() for year in ranges(step='year') if (year != tyr) and any(
					(e.get('album_id') == album_id) and (e.get('rank') == 3) for e in
					sqldb.count_scrobbles_by_album(since=year.first_stamp(),to=year.last_stamp(),resolve_ids=False,dbconn=dbconn)
				)]
			},
			"topweeks":len([
				week for week in ranges(step="week") if (week != twk) and any(
					(e.get('album_id') == album_id) and (e.get('rank') == 1) for e in
					sqldb.count_scrobbles_by_album(since=week.first_stamp(),to=week.last_stamp(),resolve_ids=False,dbconn=dbconn)
				)
			])
		})

	return {
		"album":album,
		"scrobbles":scrobbles,
		"certification":cert,
		"id":album_id,
		**extrainfo
	}



### TODO: FIND COOL ALGORITHM TO SELECT FEATURED STUFF
@waitfordb
def get_featured(dbconn=None):
	# temporary stand-in
	ranges = [
		MTRangeComposite(since=today().next(-14),to=today()),
		MTRangeComposite(since=thisweek().next(-12),to=thisweek()),
		MTRangeComposite(since=thisweek().next(-52),to=thisweek()),
		alltime()
	]
	funcs = {
		"artist": (get_charts_artists,{'associated':False}),
		"album": (get_charts_albums,{}),
		"track": (get_charts_tracks,{})
	}
	result = {t:None for t in funcs}

	for entity_type in funcs:
		for r in ranges:
			func,kwargs = funcs[entity_type]
			chart = func(timerange=r,**kwargs)
			if chart:
				result[entity_type] = chart[0][entity_type]
				break
	return result

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
	upgrade.parse_old_albums()

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

	dbstatus['complete'] = True

	# cache some stuff that we'll probably need
	with sqldb.engine.connect() as dbconn:
		with dbconn.begin():
			for week in ranges(step='week'):
				sqldb.count_scrobbles_by_artist(since=week.first_stamp(),to=week.last_stamp(),resolve_ids=False,associated=True,dbconn=dbconn)
				sqldb.count_scrobbles_by_track(since=week.first_stamp(),to=week.last_stamp(),resolve_ids=False,dbconn=dbconn)
				sqldb.count_scrobbles_by_album(since=week.first_stamp(),to=week.last_stamp(),resolve_ids=False,dbconn=dbconn)




# Search for strings
def db_search(query,type=None):
	results = []
	if type=="ARTIST":
		results = sqldb.search_artist(query)
	if type=="TRACK":
		results = sqldb.search_track(query)
	if type=="ALBUM":
		results = sqldb.search_album(query)

	return results
