# server
from bottle import request, response, FormsDict, HTTPError

# rest of the project
from ..cleanup import CleanerAgent, CollectorAgent
from .. import utilities
from ..malojatime import register_scrobbletime, time_stamps, ranges, alltime
from ..malojauri import uri_to_internal, internal_to_uri, compose_querystring
from ..thirdparty import proxy_scrobble_all
from ..globalconf import data_dir, malojaconfig, apikeystore
#db
from . import sqldb

# doreah toolkit
from doreah.logging import log
from doreah import tsv
from doreah.caching import Cache, DeepCache
from doreah.auth import authenticated_api, authenticated_api_with_alternate
from doreah.io import ProgressBar
try:
	from doreah.persistence import DiskDict
except: pass
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
from importlib.machinery import SourceFileLoader
import urllib



dbstatus = {
	"healthy":False,
	"rebuildinprogress":False,
	"complete":False
}
class DatabaseNotBuilt(HTTPError):
	def __init__(self):
		super().__init__(
			status=503,
			body="The Maloja Database is being upgraded to Version 3. This could take several minutes.",
			headers={"Retry-After":120}
		)


def waitfordb(func):
	def newfunc(*args,**kwargs):
		if not dbstatus['healthy']: raise DatabaseNotBuilt()
		return func(*args,**kwargs)
	return newfunc



MEDALS_ARTISTS = {}	#literally only changes once per year, no need to calculate that on the fly
MEDALS_TRACKS = {}
WEEKLY_TOPTRACKS = {}
WEEKLY_TOPARTISTS = {}

ISSUES = {}

cla = CleanerAgent()
coa = CollectorAgent()




def createScrobble(artists,title,time,album=None,duration=None,volatile=False):

	if len(artists) == 0 or title == "":
		return {}

	scrobbledict = {
		"time":time,
		"track":{
			"artists":artists,
			"title":title,
			"album":{
				"name":album,
				"artists":None
			},
			"length":None
		},
		"duration":duration,
		"origin":"generic"
	}

	add_scrobble(scrobbledict)
	proxy_scrobble_all(artists,title,time)
	return scrobbledict










@waitfordb
def get_scrobbles(**keys):
	(since,to) = keys.get('timerange').timestamps()
	if 'artist' in keys:
		result = sqldb.get_scrobbles_of_artist(artist=keys['artist'],since=since,to=to)
	elif 'track' in keys:
		result = sqldb.get_scrobbles_of_track(track=keys['track'],since=since,to=to)
	else:
		result = sqldb.get_scrobbles(since=since,to=to)
	#return result[keys['page']*keys['perpage']:(keys['page']+1)*keys['perpage']]
	return list(reversed(result))

@waitfordb
def get_scrobbles_num(**keys):
	return len(get_scrobbles(**keys))

@waitfordb
def get_tracks(artist=None):
	if artist is None:
		result = sqldb.get_tracks()
	else:
		result = sqldb.get_tracks_of_artist(artist)
	return result

@waitfordb
def get_artists():
	return sqldb.get_artists()


@waitfordb
def get_charts_artists(**keys):
	(since,to) = keys.get('timerange').timestamps()
	result = sqldb.count_scrobbles_by_artist(since=since,to=to)
	return result

@waitfordb
def get_charts_tracks(**keys):
	(since,to) = keys.get('timerange').timestamps()
	if 'artist' in keys:
		result = sqldb.count_scrobbles_by_track_of_artist(since=since,to=to,artist=keys['artist'])
	else:
		result = sqldb.count_scrobbles_by_track(since=since,to=to)
	return result

@waitfordb
def get_pulse(**keys):

	rngs = ranges(**{k:keys[k] for k in keys if k in ["since","to","within","timerange","step","stepn","trail"]})
	results = []
	for rng in rngs:
		res = get_scrobbles_num(timerange=rng,**{k:keys[k] for k in keys if k != 'timerange'})
		results.append({"range":rng,"scrobbles":res})

	return results

@waitfordb
def get_performance(**keys):

	rngs = ranges(**{k:keys[k] for k in keys if k in ["since","to","within","timerange","step","stepn","trail"]})
	results = []

	for rng in rngs:
		if "track" in keys:
			track = sqldb.get_track(sqldb.get_track_id(keys['track']))
			charts = get_charts_tracks(timerange=rng)
			rank = None
			for c in charts:
				if c["track"] == track:
					rank = c["rank"]
					break
		elif "artist" in keys:
			artist = sqldb.get_artist(sqldb.get_artist_id(keys['artist']))
			# ^this is the most useless line in programming history
			# but I like consistency
			charts = get_charts_artists(timerange=rng)
			rank = None
			for c in charts:
				if c["artist"] == artist:
					rank = c["rank"]
					break
		results.append({"range":rng,"rank":rank})

	return results

@waitfordb
def get_top_artists(**keys):

	rngs = ranges(**{k:keys[k] for k in keys if k in ["since","to","within","timerange","step","stepn","trail"]})
	results = []

	for rng in rngs:
		try:
			res = get_charts_artists(timerange=rng)[0]
			results.append({"range":rng,"artist":res["artist"],"scrobbles":res["scrobbles"]})
		except:
			results.append({"range":rng,"artist":None,"scrobbles":0})

	return results


@waitfordb
def get_top_tracks(**keys):

	rngs = ranges(**{k:keys[k] for k in keys if k in ["since","to","within","timerange","step","stepn","trail"]})
	results = []

	for rng in rngs:
		try:
			res = get_charts_tracks(timerange=rng)[0]
			results.append({"range":rng,"track":res["track"],"scrobbles":res["scrobbles"]})
		except:
			results.append({"range":rng,"track":None,"scrobbles":0})

	return results

@waitfordb
def artist_info(artist):

	artist = sqldb.get_artist(sqldb.get_artist_id(artist))
	alltimecharts = get_charts_artists(timerange=alltime())
	scrobbles = get_scrobbles_num(artist=artist,timerange=alltime())
	#we cant take the scrobble number from the charts because that includes all countas scrobbles
	try:
		c = [e for e in alltimecharts if e["artist"] == artist][0]
		others = sqldb.get_associated_artists(artist)
		position = c["rank"]
		performance_weekly = get_performance(artist=artist,step="week")[:-1] #current week doesn't count
		performance_yearly = get_performance(artist=artist,step="year")[:-1] #current year doesn't count
		return {
			"artist":artist,
			"scrobbles":scrobbles,
			"position":position,
			"associated":others,
			"medals":{
				"gold":[e['range'] for e in performance_yearly if e['rank'] == 1],
				"silver":[e['range'] for e in performance_yearly if e['rank'] == 2],
				"bronze":[e['range'] for e in performance_yearly if e['rank'] == 3]
			},
			"topweeks":len([e for e in performance_weekly if e['rank'] == 1])
		}
	except:
		# if the artist isnt in the charts, they are not being credited and we
		# need to show information about the credited one
		artist = sqldb.get_credited_artists(artist)[0]
		c = [e for e in alltimecharts if e["artist"] == artist][0]
		position = c["rank"]
		return {"replace":artist,"scrobbles":scrobbles,"position":position}




@waitfordb
def track_info(track):

	track = sqldb.get_track(sqldb.get_track_id(track))
	alltimecharts = get_charts_tracks(timerange=alltime())
	#scrobbles = get_scrobbles_num(track=track,timerange=alltime())

	c = [e for e in alltimecharts if e["track"] == track][0]
	scrobbles = c["scrobbles"]
	position = c["rank"]
	cert = None
	threshold_gold, threshold_platinum, threshold_diamond = malojaconfig["SCROBBLES_GOLD","SCROBBLES_PLATINUM","SCROBBLES_DIAMOND"]
	if scrobbles >= threshold_diamond: cert = "diamond"
	elif scrobbles >= threshold_platinum: cert = "platinum"
	elif scrobbles >= threshold_gold: cert = "gold"

	performance_weekly = get_performance(track=track,step="week")[:-1] #current week doesn't count
	performance_yearly = get_performance(track=track,step="year")[:-1] #current year doesn't count


	return {
		"track":track,
		"scrobbles":scrobbles,
		"position":position,
		"medals":{
			"gold":[e['range'] for e in performance_yearly if e['rank'] == 1],
			"silver":[e['range'] for e in performance_yearly if e['rank'] == 2],
			"bronze":[e['range'] for e in performance_yearly if e['rank'] == 3]
		},
		"certification":cert,
		"topweeks":len([e for e in performance_weekly if e['rank'] == 1])
	}



def incoming_scrobble(artists,title,album=None,duration=None,time=None,fix=True):
	if time is None:
		time = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp())

	log("Incoming scrobble (): ARTISTS: " + str(artists) + ", TRACK: " + title,module="debug")
	if fix:
		(artists,title) = cla.fullclean(artists,title)
	trackdict = createScrobble(artists,title,time,album,duration)

	sync()

	return {"status":"success","track":trackdict}









def issues():
	return ISSUES

def check_issues():
	combined = []
	duplicates = []
	newartists = []

	import itertools
	import difflib

	sortedartists = ARTISTS.copy()
	sortedartists.sort(key=len,reverse=True)
	reversesortedartists = sortedartists.copy()
	reversesortedartists.reverse()
	for a in reversesortedartists:

		nochange = cla.confirmedReal(a)

		st = a
		lis = []
		reachedmyself = False
		for ar in sortedartists:
			if (ar != a) and not reachedmyself:
				continue
			elif not reachedmyself:
				reachedmyself = True
				continue

			if (ar.lower() == a.lower()) or ("the " + ar.lower() == a.lower()) or ("a " + ar.lower() == a.lower()):
				duplicates.append((ar,a))
				break

			if (ar + " " in st) or (" " + ar in st):
				lis.append(ar)
				st = st.replace(ar,"").strip()
			elif (ar == st):
				lis.append(ar)
				st = ""
				if not nochange:
					combined.append((a,lis))
				break

			elif (ar in st) and len(ar)*2 > len(st):
				duplicates.append((a,ar))

		st = st.replace("&","").replace("and","").replace("with","").strip()
		if st not in ["", a]:
			if len(st) < 5 and len(lis) == 1:
				#check if we havent just randomly found the string in another word
				#if (" " + st + " ") in lis[0] or (lis[0].endswith(" " + st)) or (lis[0].startswith(st + " ")):
				duplicates.append((a,lis[0]))
			elif len(st) < 5 and len(lis) > 1 and not nochange:
				combined.append((a,lis))
			elif len(st) >= 5 and not nochange:
				#check if we havent just randomly found the string in another word
				if (" " + st + " ") in a or (a.endswith(" " + st)) or (a.startswith(st + " ")):
					newartists.append((st,a,lis))

	#for c in itertools.combinations(ARTISTS,3):
	#	l = list(c)
	#	print(l)
	#	l.sort(key=len,reverse=True)
	#	[full,a1,a2] = l
	#	if (a1 + " " + a2 in full) or (a2 + " " + a1 in full):
	#		combined.append((full,a1,a2))


	#for c in itertools.combinations(ARTISTS,2):
	#	if
	#
	#	if (c[0].lower == c[1].lower):
	#		duplicates.append((c[0],c[1]))


	#	elif (c[0] + " " in c[1]) or (" " + c[0] in c[1]) or (c[1] + " " in c[0]) or (" " + c[1] in c[0]):
	#		if (c[0] in c[1]):
	#			full, part = c[1],c[0]
	#			rest = c[1].replace(c[0],"").strip()
	#		else:
	#			full, part = c[0],c[1]
	#			rest = c[0].replace(c[1],"").strip()
	#		if rest in ARTISTS and full not in [c[0] for c in combined]:
	#			combined.append((full,part,rest))

	#	elif (c[0] in c[1]) or (c[1] in c[0]):
	#		duplicates.append((c[0],c[1]))


	return {"duplicates":duplicates,"combined":combined,"newartists":newartists}



def get_predefined_rulesets():
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
			except:
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
	from .. import upgrade
	upgrade.upgrade_db(sqldb.add_scrobbles)

	from . import associated
	associated.load_associated_rules()

	dbstatus['healthy'] = True
	dbstatus['complete'] = True

	firstscrobble = sqldb.get_scrobbles()[0]
	register_scrobbletime(firstscrobble['time'])






# Search for strings
def db_search(query,type=None):
	results = []
	if type=="ARTIST":
		results = [a for a in ARTISTS if simplestr(query) in simplestr(a)]
	if type=="TRACK":
		results = [
		    get_track_dict(t) for t in TRACKS if simplestr(query) in simplestr(t[1])
		]
	return results


####
## Useful functions
####




# makes a string usable for searching (special characters are blanks, accents and stuff replaced with their real part)
def simplestr(input,ignorecapitalization=True):
	norm = unicodedata.normalize("NFKD",input)
	norm = [c for c in norm if not unicodedata.combining(c)]
	norm = [c if len(c.encode())==1 else " " for c in norm]
	clear = ''.join(c for c in norm)
	if ignorecapitalization: clear = clear.lower()
	return clear



#def getArtistId(nameorid):
#	if isinstance(nameorid,int):
#		return nameorid
#	else:
#		try:
#			return ARTISTS.index(nameorid)
#		except:
#			return -1


def insert(list_,item,key=lambda x:x):
	i = 0
	while len(list_) > i:
		if key(list_[i]) > key(item):
			list_.insert(i,item)
			return i
		i += 1

	list_.append(item)
	return i


def scrobbles_in_range(start,end,reverse=False):
	if reverse:
		for stamp in reversed(STAMPS):
			#print("Checking " + str(stamp))
			if stamp < start: return
			if stamp > end: continue
			yield SCROBBLESDICT[stamp]
	else:
		for stamp in STAMPS:
			#print("Checking " + str(stamp))
			if stamp < start: continue
			if stamp > end: return
			yield SCROBBLESDICT[stamp]
