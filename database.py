from bottle import Bottle, route, get, post, run, template, static_file, request, response, FormsDict
from importlib.machinery import SourceFileLoader
import urllib
import waitress
import os
import datetime
from cleanup import *
from utilities import *
from malojatime import *
import sys
import unicodedata
import json

dbserver = Bottle()


SCROBBLES = []	# Format: tuple(track_ref,timestamp,saved)
ARTISTS = []	# Format: artist
TRACKS = []	# Format: tuple(frozenset(artist_ref,...),title)

### OPTIMIZATION
SCROBBLESDICT = {}	# timestamps to scrobble mapping
STAMPS = []		# sorted
STAMPS_SET = set()	# as set for easier check if exists

cla = CleanerAgent()
coa = CollectorAgent()
clients = []

lastsync = 0

# rulestate that the entire current database was built with, or False if the database was built from inconsistent scrobble files
db_rulestate = False



### symmetric keys are fine for now since we hopefully use HTTPS
def loadAPIkeys():
	global clients
	createTSV("clients/authenticated_machines.tsv")
	clients = parseTSV("clients/authenticated_machines.tsv","string","string")
	log("Authenticated Machines: " + ", ".join([m[1] for m in clients]))

def checkAPIkey(k):
	return (k in [k for [k,d] in clients])


####
## Getting dict representations of database objects
####

def getScrobbleObject(o):
	track = getTrackObject(TRACKS[o[0]])
	return {"artists":track["artists"],"title":track["title"],"time":o[1]}
	
def getArtistObject(o):
	return o
	
def getTrackObject(o):
	artists = [getArtistObject(ARTISTS[a]) for a in o[0]]
	return {"artists":artists,"title":o[1]}


####
## Creating or finding existing database entries
####


	
def createScrobble(artists,title,time,volatile=False):
	while (time in STAMPS_SET):
		time += 1
	STAMPS_SET.add(time)
	i = getTrackID(artists,title)
	obj = (i,time,volatile) # if volatile generated, we simply pretend we have already saved it to disk
	#SCROBBLES.append(obj)
	# immediately insert scrobble correctly so we can guarantee sorted list
	index = insert(SCROBBLES,obj,key=lambda x:x[1])
	SCROBBLESDICT[time] = obj
	STAMPS.insert(index,time) #should be same index as scrobblelist
	register_scrobbletime(time)
	invalidate_caches()


def readScrobble(artists,title,time):
	while (time in STAMPS_SET):
		time += 1
	STAMPS_SET.add(time)
	i = getTrackID(artists,title)
	obj = (i,time,True)
	SCROBBLES.append(obj)
	#STAMPS.append(time)
	
	

def getArtistID(name):

	obj = name
	objlower = name.lower()
	
	try:
		return ARTISTS.index(obj)
	except:
		pass
	try:
		return [a.lower() for a in ARTISTS].index(objlower)
	except:
		i = len(ARTISTS)
		ARTISTS.append(obj)
		return i
			
def getTrackID(artists,title):
	artistset = set()
	for a in artists:
		artistset.add(getArtistID(name=a))
	obj = (frozenset(artistset),title)
	objlower = (frozenset(artistset),title.lower())
	
	try:
		return TRACKS.index(obj)
	except:
		pass
	try:
		# not the best performance
		return [(t[0],t[1].lower()) for t in TRACKS].index(objlower)
	except:
		i = len(TRACKS)
		TRACKS.append(obj)
		return i








########
########
## HTTP requests and their associated functions
########
########




@dbserver.route("/test")
def test_server():
	apikey = request.query.get("key")
	response.set_header("Access-Control-Allow-Origin","*")
	if apikey is not None and not (checkAPIkey(apikey)):
		response.status = 403
		return "Wrong API key"
	
	elif db_rulestate:
		response.status = 204
		return
	else:
		response.status = 205
		return
		
	# 204	Database server is up and operational
	# 205	Database server is up, but DB is not fully built or is inconsistent
	# 403	Database server is up, but provided API key is not valid


## All database functions are separated - the external wrapper only reads the request keys, converts them into lists and renames them where necessary, and puts the end result in a dict if not already so it can be returned as json

@dbserver.route("/scrobbles")
def get_scrobbles_external():
	keys = FormsDict.decode(request.query)
	ckeys = {}
	ckeys["artists"], ckeys["title"] = keys.getall("artist"), keys.get("title")
	ckeys["since"], ckeys["to"], ckeys["within"] = keys.get("since"), keys.get("to"), keys.get("in")
	ckeys["associated"] = (keys.get("associated")!=None)
	ckeys["max_"] = keys.get("max")
	
	result = get_scrobbles(**ckeys)
	return {"list":result}

def get_scrobbles(**keys):
	r = db_query(**{k:keys[k] for k in keys if k in ["artist","artists","title","since","to","within","associated","track"]})
	r.reverse()
	
	if keys.get("max_") is not None:
		return r[:int(keys.get("max_"))]
	else:
		return r






# UNUSED
#@dbserver.route("/amounts")
#def get_amounts_external():
#	return get_amounts() #really now
#
#def get_amounts():
#	return {"scrobbles":len(SCROBBLES),"tracks":len(TRACKS),"artists":len(ARTISTS)}
	

@dbserver.route("/numscrobbles")
def get_scrobbles_num_external():
	keys = FormsDict.decode(request.query)
	ckeys = {}
	ckeys["artists"], ckeys["title"] = keys.getall("artist"), keys.get("title")
	ckeys["since"], ckeys["to"], ckeys["within"] = keys.get("since"), keys.get("to"), keys.get("in")
	ckeys["associated"] = (keys.get("associated")!=None)
	
	result = get_scrobbles_num(**ckeys)
	return {"amount":result}

def get_scrobbles_num(**keys):
	r = db_query(**{k:keys[k] for k in keys if k in ["artist","track","artists","title","since","to","within","associated"]})
	return len(r)


# UNUSED
#@dbserver.route("/charts")
#def get_charts_external():
#	keys = FormsDict.decode(request.query)
#	ckeys = {}
#	ckeys["since"], ckeys["to"], ckeys["within"] = keys.get("since"), keys.get("to"), keys.get("in")
#	
#	result = get_scrobbles_num(**ckeys)	
#	return {"number":result}

#def get_charts(**keys):
#	return db_aggregate(**{k:keys[k] for k in keys if k in ["since","to","within"]})







@dbserver.route("/tracks")
def get_tracks_external():
	keys = FormsDict.decode(request.query)
	ckeys = {}
	ckeys["artist"] = keys.get("artist")

	result = get_tracks(**ckeys)
	return {"list":result}

def get_tracks(artist=None):
	
	if artist is not None:
		artistid = ARTISTS.index(artist)
	else:
		artistid = None

	# Option 1
	return [getTrackObject(t) for t in TRACKS if (artistid in t[0]) or (artistid==None)]
	
	# Option 2 is a bit more elegant but much slower
	#tracklist = [getTrackObject(t) for t in TRACKS]
	#ls = [t for t in tracklist if (artist in t["artists"]) or (artist==None)]


@dbserver.route("/artists")
def get_artists_external():
	result = get_artists()
	return {"list":result}

def get_artists():
	return ARTISTS #well
	





	
@dbserver.route("/charts/artists")
def get_charts_artists_external():
	keys = FormsDict.decode(request.query)
	ckeys = {}
	ckeys["since"], ckeys["to"], ckeys["within"] = keys.get("since"), keys.get("to"), keys.get("in")
	
	result = get_charts_artists(**ckeys)
	return {"list":result}

def get_charts_artists(**keys):
	return db_aggregate(by="ARTIST",**{k:keys[k] for k in keys if k in ["since","to","within"]})






@dbserver.route("/charts/tracks")
def get_charts_tracks_external():
	keys = FormsDict.decode(request.query)
	ckeys = {}
	ckeys["since"], ckeys["to"], ckeys["within"] = keys.get("since"), keys.get("to"), keys.get("in")
	ckeys["artist"] = keys.get("artist")
	
	result = get_charts_tracks(**ckeys)
	return {"list":result}
	
def get_charts_tracks(**keys):
	return db_aggregate(by="TRACK",**{k:keys[k] for k in keys if k in ["since","to","within","artist"]})
	
	
	





	
@dbserver.route("/pulse")
def get_pulse_external():
	keys = FormsDict.decode(request.query)
	ckeys = {}
	ckeys["since"], ckeys["to"], ckeys["within"] = keys.get("since"), keys.get("to"), keys.get("in")
	ckeys["step"], ckeys["trail"] = keys.get("step"), int_or_none(keys.get("trail"))
	ckeys["artists"], ckeys["title"] = keys.getall("artist"), keys.get("title")
	ckeys["associated"] = (keys.get("associated")!=None)
	if ckeys["step"] is not None: [ckeys["step"],ckeys["stepn"]] = (ckeys["step"].split("-") + [1])[:2]	# makes the multiplier 1 if not assigned
	if "stepn" in ckeys: ckeys["stepn"] = int(ckeys["stepn"])
	
	cleandict(ckeys)
	results = get_pulse(**ckeys)
	return {"list":results}

def get_pulse(**keys):

	rngs = ranges(**{k:keys[k] for k in keys if k in ["since","to","within","step","stepn","trail"]})	
	results = []
	
	for (a,b) in rngs:
		res = len(db_query(since=a,to=b,**{k:keys[k] for k in keys if k in ["artists","artist","track","title","associated"]}))
		results.append({"from":a,"to":b,"scrobbles":res})
		
	return results






		
	
@dbserver.route("/top/artists")
def get_top_artists_external():

	keys = FormsDict.decode(request.query)
	ckeys = {}
	ckeys["since"], ckeys["to"], ckeys["within"] = keys.get("since"), keys.get("to"), keys.get("in")
	ckeys["step"], ckeys["trail"] = keys.get("step"), int_or_none(keys.get("trail"))
	if ckeys["step"] is not None: [ckeys["step"],ckeys["stepn"]] = (ckeys["step"].split("-") + [1])[:2]	# makes the multiplier 1 if not assigned
	if "stepn" in ckeys: ckeys["stepn"] = int(ckeys["stepn"])
	
	cleandict(ckeys)
	results = get_top_artists(**ckeys)
	return {"list":results}
	
def get_top_artists(**keys):
	
	rngs = ranges(**{k:keys[k] for k in keys if k in ["since","to","within","step","stepn","trail"]})
	results = []
		
	for (a,b) in rngs:
		try:
			res = db_aggregate(since=a,to=b,by="ARTIST")[0]
			results.append({"from":a,"to":b,"artist":res["artist"],"scrobbles":res["scrobbles"]})
		except:
			results.append({"from":a,"to":b,"artist":None,"scrobbles":0})
	
	return results










@dbserver.route("/top/tracks")
def get_top_tracks_external():
	keys = FormsDict.decode(request.query)
	ckeys = {}
	ckeys["since"], ckeys["to"], ckeys["within"] = keys.get("since"), keys.get("to"), keys.get("in")
	ckeys["step"], ckeys["trail"] = keys.get("step"), int_or_none(keys.get("trail"))
	if ckeys["step"] is not None: [ckeys["step"],ckeys["stepn"]] = (ckeys["step"].split("-") + [1])[:2]	# makes the multiplier 1 if not assigned
	if "stepn" in ckeys: ckeys["stepn"] = int(ckeys["stepn"])
	
	cleandict(ckeys)
	results = get_top_tracks(**ckeys)
	return {"list":results}

def get_top_tracks(**keys):

	rngs = ranges(**{k:keys[k] for k in keys if k in ["since","to","within","step","stepn","trail"]})
	results = []
		
	for (a,b) in rngs:
		try:
			res = db_aggregate(since=a,to=b,by="TRACK")[0]
			results.append({"from":a,"to":b,"track":res["track"],"scrobbles":res["scrobbles"]})
		except:
			results.append({"from":a,"to":b,"track":None,"scrobbles":0})
	
	return results







	
	
	
		
@dbserver.route("/artistinfo")
def artistInfo_external():
	keys = FormsDict.decode(request.query)
	ckeys = {}
	ckeys["artist"] = keys.get("artist")
	
	results = artistInfo(**ckeys)
	return results
	
def artistInfo(artist):
	
	charts = db_aggregate(by="ARTIST")
	scrobbles = len(db_query(artists=[artist])) #we cant take the scrobble number from the charts because that includes all countas scrobbles
	try:
		c = [e for e in charts if e["artist"] == artist][0]
		others = coa.getAllAssociated(artist)
		return {"scrobbles":scrobbles,"position":charts.index(c) + 1,"associated":others}
	except:
		# if the artist isnt in the charts, they are not being credited and we need to show information about the credited one
		artist = coa.getCredited(artist)
		c = [e for e in charts if e["artist"] == artist][0]
		return {"replace":artist,"scrobbles":scrobbles,"position":charts.index(c) + 1}
	
	
	
	
		
@dbserver.route("/trackinfo")	
def trackInfo_external():
	keys = FormsDict.decode(request.query)
	ckeys = {}
	ckeys["artists"],ckeys["title"] = keys.getall("artist"), keys.get("title")
	
	results = trackInfo(**ckeys)
	return results

def trackInfo(artists,title):
	charts = db_aggregate(by="TRACK")
	scrobbles = len(db_query(artists=artists,title=title)) #we cant take the scrobble number from the charts because that includes all countas scrobbles
	
	c = [e for e in charts if set(e["track"]["artists"]) == set(artists) and e["track"]["title"] == title][0]
	return {"scrobbles":scrobbles,"position":charts.index(c) + 1}







@dbserver.get("/newscrobble")
def pseudo_post_scrobble():
	keys = FormsDict.decode(request.query) # The Dal★Shabet handler
	artists = keys.get("artist")
	title = keys.get("title")
	apikey = keys.get("key")
	if not (checkAPIkey(apikey)):
		response.status = 403
		return ""
	try:
		time = int(keys.get("time"))
	except:
		time = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp())
	(artists,title) = cla.fullclean(artists,title)

	## this is necessary for localhost testing
	response.set_header("Access-Control-Allow-Origin","*")
	
	createScrobble(artists,title,time)
	
	if (time - lastsync) > 3600:
		sync()
	
	return ""
	
@dbserver.post("/newscrobble")
def post_scrobble():
	keys = FormsDict.decode(request.forms) # The Dal★Shabet handler
	artists = keys.get("artist")
	title = keys.get("title")
	apikey = keys.get("key")
	if not (checkAPIkey(apikey)):
		response.status = 403
		return ""
	
	try:
		time = int(keys.get("time"))
	except:
		time = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp())
	(artists,title) = cla.fullclean(artists,title)

	## this is necessary for localhost testing
	response.set_header("Access-Control-Allow-Origin","*")
	
	createScrobble(artists,title,time)
	
	#if (time - lastsync) > 3600:
	#	sync()
	sync() #let's just always sync, not like one filesystem access every three minutes is a problem and it avoids lost tracks when we lose power
	
	return ""
	
@dbserver.route("/sync")
def abouttoshutdown():
	sync()
	#sys.exit()

@dbserver.post("/newrule")
def newrule():
	keys = FormsDict.decode(request.forms)
	apikey = keys.pop("key",None)
	if (checkAPIkey(apikey)):
		addEntry("rules/webmade.tsv",[k for k in keys])
		global db_rulestate
		db_rulestate = False
	
	
@dbserver.route("/issues")
def issues_external(): #probably not even needed
	return issues()
	
	
def issues():
	combined = []
	duplicates = []
	newartists = []
	inconsistent = not db_rulestate
	# if the user manually edits files while the server is running this won't show, but too lazy to check the rulestate here
	
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
		if st != "" and st != a:
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
			
	
	return {"duplicates":duplicates,"combined":combined,"newartists":newartists,"inconsistent":inconsistent}

@dbserver.post("/rebuild")
def rebuild():
	
	keys = FormsDict.decode(request.forms)
	apikey = keys.pop("key",None)
	if (checkAPIkey(apikey)):
		log("Database rebuild initiated!")
		global db_rulestate
		db_rulestate = False
		sync()
		os.system("python3 fixexisting.py")
		global cla, coa
		cla = CleanerAgent()
		coa = CollectorAgent()
		build_db()




@dbserver.get("/search")
def search():
	keys = FormsDict.decode(request.query)
	query = keys.get("query")
	max_ = keys.get("max")
	if max_ is not None: max_ = int(max_)
	query = query.lower()
	
	artists = db_search(query,type="ARTIST")
	tracks = db_search(query,type="TRACK")
	# if the string begins with the query it's a better match, if a word in it begins with it, still good
	# also, shorter is better (because longer titles would be easier to further specify)
	artists.sort(key=lambda x: ((0 if x.lower().startswith(query) else 1 if " " + query in x.lower() else 2),len(x)))
	tracks.sort(key=lambda x: ((0 if x["title"].lower().startswith(query) else 1 if " " + query in x["title"].lower() else 2),len(x["title"])))
	return {"artists":artists[:max_],"tracks":tracks[:max_]}
	
####
## Server operation
####



# Starts the server
def runserver(PORT):
	log("Starting database server...")
	global lastsync
	lastsync = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp())
	build_db()
	

	loadAPIkeys()

	run(dbserver, host='::', port=PORT, server='waitress')
	log("Database server reachable!")

def build_db():
	
	
	log("Building database...")
	
	global SCROBBLES, ARTISTS, TRACKS
	global SCROBBLESDICT, STAMPS
	
	SCROBBLES = []
	ARTISTS = []
	TRACKS = []
	
	
	
	db = parseAllTSV("scrobbles","int","string","string",escape=False)
	for sc in db:
		artists = sc[1].split("␟")
		title = sc[2]
		time = sc[0]
		
		readScrobble(artists,title,time)

			
	SCROBBLES.sort(key = lambda tup: tup[1])
	
	SCROBBLESDICT = {obj[1]:obj for obj in SCROBBLES}
	STAMPS = [t for t in SCROBBLESDICT]
	STAMPS.sort()
	register_scrobbletime(STAMPS[0])
	
	#print(SCROBBLESDICT)
	#print(STAMPS)
	
	# get extra artists with zero scrobbles from countas rules
	for artist in coa.getAllArtists():
		if artist not in ARTISTS:
			ARTISTS.append(artist)
	
	coa.updateIDs(ARTISTS)
	
			
	global db_rulestate
	db_rulestate = consistentRulestate("scrobbles",cla.checksums)
	
	# load cached images
	loadCache()
	
	log("Database fully built!")
	


# Saves all cached entries to disk			
def sync():

	# all entries by file collected
	# so we don't open the same file for every entry
	entries = {}
	
	for idx in range(len(SCROBBLES)):
		if not SCROBBLES[idx][2]:
			
			t = getScrobbleObject(SCROBBLES[idx])
			
			artistlist = list(t["artists"])
			artistlist.sort() #we want the order of artists to be deterministic so when we update files with new rules a diff can see what has actually been changed
			artistss = "␟".join(artistlist)
			timestamp = datetime.date.fromtimestamp(t["time"])
			
			entry = [str(t["time"]),artistss,t["title"]]
			
			monthcode = str(timestamp.year) + "_" + str(timestamp.month)
			entries.setdefault(monthcode,[]).append(entry) #i feckin love the setdefault function
			
			SCROBBLES[idx] = (SCROBBLES[idx][0],SCROBBLES[idx][1],True)
			
	for e in entries:
		addEntries("scrobbles/" + e + ".tsv",entries[e],escape=False)
		combineChecksums("scrobbles/" + e + ".tsv",cla.checksums)
		
			
	global lastsync
	lastsync = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp())
	log("Database saved to disk.")
	
	# save cached images
	saveCache()
			


###
## Caches in front of DB
## these are intended mainly for excessive site navigation during one session (e.g. constantly going back to the main page to click the next link)
###


import copy

cache_query = {}
cacheday = (0,0,0)
def db_query(**kwargs):
	check_cache_age()
	global cache_query
	key = json.dumps(kwargs)
	if key in cache_query: return copy.copy(cache_query[key])
	
	result = db_query_full(**kwargs)
	cache_query[key] = copy.copy(result)
	return result

cache_aggregate = {}
def db_aggregate(**kwargs):
	check_cache_age()
	global cache_aggregate
	key = json.dumps(kwargs)
	if key in cache_aggregate: return copy.copy(cache_aggregate[key])
	
	result = db_aggregate_full(**kwargs)
	cache_aggregate[key] = copy.copy(result)
	return result
	
def invalidate_caches():
	global cache_query, cache_aggregate
	cache_query = {}
	cache_aggregate = {}
	
	now = datetime.datetime.now()
	global cacheday
	cacheday = (now.year,now.month,now.day)

def check_cache_age():
	now = datetime.datetime.now()
	global cacheday
	if cacheday != (now.year,now.month,now.day): invalidate_caches()


####
## Database queries
####



# Queries the database			
def db_query_full(artist=None,artists=None,title=None,track=None,since=None,to=None,within=None,associated=False):

	(since, to) = time_stamps(since,to,within)
	
	# this is not meant as a search function. we *can* query the db with a string, but it only works if it matches exactly	
	# if a title is specified, we assume that a specific track (with the exact artist combination) is requested
	# if not, duplicate artist arguments are ignored
	
	#artist = None
	
	if artist is not None and isinstance(artist,str):
		artist = ARTISTS.index(artist)
	
	# artists to numbers
	if artists is not None:	
		artists = set([(ARTISTS.index(a) if isinstance(a,str) else a) for a in artists])
	
	# track to number
	if track is not None and isinstance(track,dict):
		trackartists = set([(ARTISTS.index(a) if isinstance(a,str) else a) for a in track["artists"]])
		track = TRACKS.index((frozenset(trackartists),track["title"]))
		artists = None
	
	#check if track is requested via title
	if title!=None and track==None:
		track = TRACKS.index((frozenset(artists),title))
		artists = None
		
	# if we're not looking for a track (either directly or per title artist arguments, which is converted to track above)
	# we only need one artist
	elif artist is None and track is None and artists is not None and len(artists) != 0:
		artist = artists.pop()
		
			
	
		
	if associated:
		#return [getScrobbleObject(s) for s in SCROBBLES if (s[0] == track or track==None) and (artist==None or artist in coa.getCreditedList(TRACKS[s[0]][0])) and (since < s[1] < to)]
		return [getScrobbleObject(s) for s in scrobbles_in_range(since,to) if (track is None or s[0] == track) and (artist is None or artist in coa.getCreditedList(TRACKS[s[0]][0]))]
	else:
		#return [getScrobbleObject(s) for s in SCROBBLES if (s[0] == track or track==None) and (artist==None or artist in TRACKS[s[0]][0]) and (since < s[1] < to)]
		return [getScrobbleObject(s) for s in scrobbles_in_range(since,to) if (track is None or s[0] == track) and (artist is None or artist in  TRACKS[s[0]][0])]
	# pointless to check for artist when track is checked because every track has a fixed set of artists, but it's more elegant this way
	

# Queries that... well... aggregate
def db_aggregate_full(by=None,since=None,to=None,within=None,artist=None):
	(since, to) = time_stamps(since,to,within)
	
	if isinstance(artist, str):
		artist = ARTISTS.index(artist)
	
	if (by=="ARTIST"):
		#this is probably a really bad idea
		#for a in ARTISTS:
		#	num = len(db_query(artist=a,since=since,to=to))
		#	
				
		# alright let's try for real
		charts = {}
		#for s in [scr for scr in SCROBBLES if since < scr[1] < to]:
		for s in scrobbles_in_range(since,to):
			artists = TRACKS[s[0]][0]
			for a in coa.getCreditedList(artists):
				# this either creates the new entry or increments the existing one
				charts[a] = charts.setdefault(a,0) + 1
				
		ls = [{"artist":getArtistObject(ARTISTS[a]),"scrobbles":charts[a],"counting":coa.getAllAssociated(ARTISTS[a])} for a in charts]
		return sorted(ls,key=lambda k:k["scrobbles"], reverse=True)
		
	elif (by=="TRACK"):
		charts = {}
		#for s in [scr for scr in SCROBBLES if since < scr[1] < to and (artist==None or (artist in TRACKS[scr[0]][0]))]:
		for s in [scr for scr in scrobbles_in_range(since,to) if (artist is None or (artist in TRACKS[scr[0]][0]))]:
			track = s[0]
			# this either creates the new entry or increments the existing one
			charts[track] = charts.setdefault(track,0) + 1
				
		ls = [{"track":getTrackObject(TRACKS[t]),"scrobbles":charts[t]} for t in charts]
		return sorted(ls,key=lambda k:k["scrobbles"], reverse=True)
		
	else:
		#return len([scr for scr in SCROBBLES if since < scr[1] < to])
		return len(list(scrobbles_in_range(since,to)))


# Search for strings
def db_search(query,type=None):
	if type=="ARTIST":
		results = []
		for a in ARTISTS:
			#if query.lower() in a.lower():
			if simplestr(query) in simplestr(a):
				results.append(a)
	
	if type=="TRACK":
		results = []
		for t in TRACKS:
			#if query.lower() in t[1].lower():
			if simplestr(query) in simplestr(t[1]):
				results.append(getTrackObject(t))
	
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


	
def getArtistId(nameorid):
	if isinstance(nameorid,int):
		return nameorid
	else:
		try:
			return ARTISTS.index(nameorid)
		except:
			return -1
			
			
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

	#for stamp in range(start,end+1):
	#	if stamp%1000 == 0: print("testing " + str(stamp))
	#	if stamp in SCROBBLESDICT:
	#		yield SCROBBLESDICT[stamp]
	

# for performance testing
def generateStuff(num=0,pertrack=0,mult=0):
	import random
	for i in range(num):
		track = random.choice(TRACKS)
		t = getTrackObject(track)
		time = random.randint(STAMPS[0],STAMPS[-1])
		createScrobble(t["artists"],t["title"],time,volatile=True)
		
	for track in TRACKS:
		t = getTrackObject(track)
		for i in range(pertrack):
			time = random.randint(STAMPS[0],STAMPS[-1])
			createScrobble(t["artists"],t["title"],time,volatile=True)
	
	for scrobble in SCROBBLES:
		s = getScrobbleObject(scrobble)	
		for i in range(mult):
			createScrobble(s["artists"],s["title"],s["time"] - i*500,volatile=True)
