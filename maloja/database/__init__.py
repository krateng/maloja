# server
from bottle import request, response, FormsDict, HTTPError

# rest of the project
from ..cleanup import CleanerAgent, CollectorAgent
from .. import utilities
from ..malojatime import register_scrobbletime, time_stamps, ranges
from ..malojauri import uri_to_internal, internal_to_uri, compose_querystring
from ..thirdparty import proxy_scrobble_all
from ..globalconf import data_dir, malojaconfig, apikeystore
#db
from . import sqldb
from .cache import db_query, db_aggregate

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
			body="The Maloja Database is still being built. Try again in a few seconds.",
			headers={"Retry-After":10}
		)



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










########
########
## HTTP requests and their associated functions
########
########








def get_scrobbles(**keys):
	r = db_query(**{k:keys[k] for k in keys if k in ["artist","artists","title","since","to","within","timerange","associated","track"]})
	return r


def info():
	totalscrobbles = get_scrobbles_num()
	artists = {}

	return {
		"name":malojaconfig["NAME"],
		"artists":{
			chartentry["artist"]:round(chartentry["scrobbles"] * 100 / totalscrobbles,3)
			for chartentry in get_charts_artists() if chartentry["scrobbles"]/totalscrobbles >= 0
		},
		"known_servers":list(KNOWN_SERVERS)
	}



def get_scrobbles_num(**keys):
	r = db_query(**{k:keys[k] for k in keys if k in ["artist","track","artists","title","since","to","within","timerange","associated"]})
	return len(r)

def get_tracks(artist=None):

	artistid = ARTISTS.index(artist) if artist is not None else None
	return [get_track_dict(t) for t in TRACKS if (artistid in t.artists) or (artistid==None)]



def get_artists():
	if not dbstatus['healthy']: raise DatabaseNotBuilt()
	return ARTISTS #well



def get_charts_artists(**keys):
	return db_aggregate(by="ARTIST",**{k:keys[k] for k in keys if k in ["since","to","within","timerange"]})


def get_charts_tracks(**keys):
	return db_aggregate(by="TRACK",**{k:keys[k] for k in keys if k in ["since","to","within","timerange","artist"]})

def get_pulse(**keys):

	rngs = ranges(**{k:keys[k] for k in keys if k in ["since","to","within","timerange","step","stepn","trail"]})
	results = []
	for rng in rngs:
		res = len(db_query(timerange=rng,**{k:keys[k] for k in keys if k in ["artists","artist","track","title","associated"]}))
		results.append({"range":rng,"scrobbles":res})

	return results


def get_performance(**keys):

	rngs = ranges(**{k:keys[k] for k in keys if k in ["since","to","within","timerange","step","stepn","trail"]})
	results = []

	for rng in rngs:
		if "track" in keys:
			charts = get_charts_tracks(timerange=rng)
			rank = None
			for c in charts:
				if c["track"] == keys["track"]:
					rank = c["rank"]
					break
		elif "artist" in keys:
			charts = get_charts_artists(timerange=rng)
			rank = None
			for c in charts:
				if c["artist"] == keys["artist"]:
					rank = c["rank"]
					break
		results.append({"range":rng,"rank":rank})

	return results


def get_top_artists(**keys):

	rngs = ranges(**{k:keys[k] for k in keys if k in ["since","to","within","timerange","step","stepn","trail"]})
	results = []

	for rng in rngs:
		try:
			res = db_aggregate(timerange=rng,by="ARTIST")[0]
			results.append({"range":rng,"artist":res["artist"],"counting":res["counting"],"scrobbles":res["scrobbles"]})
		except:
			results.append({"range":rng,"artist":None,"scrobbles":0})

	return results









def get_top_tracks(**keys):

	rngs = ranges(**{k:keys[k] for k in keys if k in ["since","to","within","timerange","step","stepn","trail"]})
	results = []

	for rng in rngs:
		try:
			res = db_aggregate(timerange=rng,by="TRACK")[0]
			results.append({"range":rng,"track":res["track"],"scrobbles":res["scrobbles"]})
		except:
			results.append({"range":rng,"track":None,"scrobbles":0})

	return results


def artistInfo(artist):

	charts = db_aggregate(by="ARTIST")
	scrobbles = len(db_query(artists=[artist]))
	#we cant take the scrobble number from the charts because that includes all countas scrobbles
	try:
		c = [e for e in charts if e["artist"] == artist][0]
		others = [a for a in coa.getAllAssociated(artist) if a in ARTISTS]
		position = c["rank"]
		performance = get_performance(artist=artist,step="week")
		return {
			"artist":artist,
			"scrobbles":scrobbles,
			"position":position,
			"associated":others,
			"medals":{"gold":[],"silver":[],"bronze":[],**MEDALS_ARTISTS.get(artist,{})},
			"topweeks":WEEKLY_TOPARTISTS.get(artist,0)
		}
	except:
		# if the artist isnt in the charts, they are not being credited and we
		# need to show information about the credited one
		artist = coa.getCredited(artist)
		c = [e for e in charts if e["artist"] == artist][0]
		position = c["rank"]
		return {"replace":artist,"scrobbles":scrobbles,"position":position}






def trackInfo(track):
	charts = db_aggregate(by="TRACK")
	#scrobbles = len(db_query(artists=artists,title=title))	#chart entry of track always has right scrobble number, no countas rules here
	#c = [e for e in charts if set(e["track"]["artists"]) == set(artists) and e["track"]["title"] == title][0]
	c = [e for e in charts if e["track"] == track][0]
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
		"medals":{"gold":[],"silver":[],"bronze":[],**MEDALS_TRACKS.get((frozenset(track["artists"]),track["title"]),{})},
		"certification":cert,
		"topweeks":WEEKLY_TOPTRACKS.get(((frozenset(track["artists"]),track["title"])),0)
	}




def compare(remoteurl):
	import json
	compareurl = remoteurl + "/api/info"

	response = urllib.request.urlopen(compareurl)
	strangerinfo = json.loads(response.read())
	owninfo = info()

	#add_known_server(compareto)

	artists = {}

	for a in owninfo["artists"]:
		artists[a.lower()] = {"name":a,"self":int(owninfo["artists"][a]*1000),"other":0}

	for a in strangerinfo["artists"]:
		artists[a.lower()] = artists.setdefault(a.lower(),{"name":a,"self":0})
		artists[a.lower()]["other"] = int(strangerinfo["artists"][a]*1000)

	for a in artists:
		common = min(artists[a]["self"],artists[a]["other"])
		artists[a]["self"] -= common
		artists[a]["other"] -= common
		artists[a]["common"] = common

	best = sorted((artists[a]["name"] for a in artists),key=lambda x: artists[x.lower()]["common"],reverse=True)

	result = {
		"unique_self":sum(artists[a]["self"] for a in artists if artists[a]["common"] == 0),
		"more_self":sum(artists[a]["self"] for a in artists if artists[a]["common"] != 0),
		"common":sum(artists[a]["common"] for a in artists),
		"more_other":sum(artists[a]["other"] for a in artists if artists[a]["common"] != 0),
		"unique_other":sum(artists[a]["other"] for a in artists if artists[a]["common"] == 0)
	}

	total = sum(result[c] for c in result)

	for r in result:
		result[r] = (result[r],result[r]/total)



	return {
		"result":result,
		"info":{
			"ownname":owninfo["name"],
			"remotename":strangerinfo["name"]
		},
		"commonartist":best[0]
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
	dbstatus['healthy'] = True
	dbstatus['complete'] = True









####
## Database queries
####



# Queries the database
def db_query_full(artist=None,artists=None,title=None,track=None,timerange=None,associated=False,max_=None):
	print((artist,artists,title,track,timerange))
	if not dbstatus['healthy']: raise DatabaseNotBuilt()
	(since, to) = time_stamps(range=timerange)

	if artists is not None and title is not None:
		print(col['red']("THIS SHOULD NO LONGER HAPPEN"))
		track = {'artists':artists,'title':title}

	if track is not None:
		return sqldb.get_scrobbles_of_track(track=track,since=since,to=to)

	if artist is not None:
		return sqldb.get_scrobbles_of_artist(artist=artist,since=since,to=to)

	return sqldb.get_scrobbles(since=since,to=to)



# Queries that... well... aggregate
def db_aggregate_full(by=None,timerange=None,artist=None):

	if not dbstatus['healthy']: raise DatabaseNotBuilt()
	(since, to) = time_stamps(range=timerange)


	if (by=="ARTIST"):

		trackcharts = {}
		charts = {}
		scrobbles = sqldb.get_scrobbles(since=since,to=to,resolve_references=False)

		for s in scrobbles:
			trackcharts[s['track']] = trackcharts.setdefault(s['track'],0) + 1

		for t in trackcharts:
			artists = sqldb.get_artists_of_track(t,resolve_references=False)
			for a in coa.getCreditedList(artists):
				charts[a] = charts.setdefault(a,0) + trackcharts[t]


		ls = [{"artist":sqldb.get_artist(a),"scrobbles":charts[a],"counting":[]} for a in charts]
		ls.sort(key=lambda k:k["scrobbles"],reverse=True)
		# add ranks
		for rnk in range(len(ls)):
			if rnk == 0 or ls[rnk]["scrobbles"] < ls[rnk-1]["scrobbles"]:
				ls[rnk]["rank"] = rnk + 1
			else:
				ls[rnk]["rank"] = ls[rnk-1]["rank"]
		return ls

	elif (by=="TRACK"):
		charts = {}
		if artist is None:
			scrobbles = sqldb.get_scrobbles(since=since,to=to,resolve_references=False)
		else:
			scrobbles = sqldb.get_scrobbles_of_artist(since=since,to=to,artist=artist,resolve_references=False)

		for s in scrobbles:
			charts[s['track']] = charts.setdefault(s['track'],0) + 1


		ls = [{"track":sqldb.get_track(t),"scrobbles":charts[t]} for t in charts]
		ls.sort(key=lambda k:k["scrobbles"],reverse=True)
		# add ranks
		for rnk in range(len(ls)):
			if rnk == 0 or ls[rnk]["scrobbles"] < ls[rnk-1]["scrobbles"]:
				ls[rnk]["rank"] = rnk + 1
			else:
				ls[rnk]["rank"] = ls[rnk-1]["rank"]
		return ls

	else:
		#return len([scr for scr in SCROBBLES if since < scr[1] < to])
		return len(list(scrobbles_in_range(since,to)))


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
