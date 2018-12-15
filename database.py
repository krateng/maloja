from bottle import route, get, post, run, template, static_file, request, response, FormsDict
from importlib.machinery import SourceFileLoader
import urllib
import waitress
import os
import datetime
from cleanup import *
from utilities import *
import sys


SCROBBLES = []	# Format: tuple(track_ref,timestamp,saved)
ARTISTS = []	# Format: artist
TRACKS = []	# Format: tuple(frozenset(artist_ref,...),title)

timestamps = set()

c = CleanerAgent()
sovereign = CollectorAgent()
clients = []

lastsync = 0


### symmetric keys are fine for now since we hopefully use HTTPS
def loadAPIkeys():
	global clients
	createTSV("clients/authenticated_machines.tsv")
	clients = parseTSV("clients/authenticated_machines.tsv","string","string")

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


	
def createScrobble(artists,title,time):
	while (time in timestamps):
		time += 1
	timestamps.add(time)
	i = getTrackID(artists,title)
	obj = (i,time,False)
	SCROBBLES.append(obj)


def readScrobble(artists,title,time):
	while (time in timestamps):
		time += 1
	timestamps.add(time)
	i = getTrackID(artists,title)
	obj = (i,time,True)
	SCROBBLES.append(obj)
	

def getArtistID(name):

	obj = name
	try:
		i = ARTISTS.index(obj)
	except:
		i = len(ARTISTS)
		ARTISTS.append(obj)
	return i
			
def getTrackID(artists,title):
	artistset = set()
	for a in artists:
		artistset.add(getArtistID(name=a))
	obj = (frozenset(artistset),title)
	
	try:
		i = TRACKS.index(obj)
	except:
		i = len(TRACKS)
		TRACKS.append(obj)
	return i


####
## HTTP requests
####

@route("/test")
def test_server():
	apikey = request.query.get("key")
	response.set_header("Access-Control-Allow-Origin","*")
	if not (checkAPIkey(apikey)):
		response.status = 403
		return "Wrong or Missing API key"
	
	else:
		response.status = 204
		return

@route("/scrobbles")
def get_scrobbles():
	keys = request.query
	r = db_query(artist=keys.get("artist"),track=keys.get("track"),since=keys.get("since"),to=keys.get("to"))

	return {"list":r} ##json can't be a list apparently???

@route("/tracks")
def get_tracks():
	artist = request.query.get("artist")
	
	if artist is not None:
		artistid = ARTISTS.index(artist)
	
	# Option 1
	ls = [getTrackObject(t) for t in TRACKS if (artistid in t[0]) or (artistid==None)]
	
	# Option 2 is a bit more elegant but much slower
	#tracklist = [getTrackObject(t) for t in TRACKS]
	#ls = [t for t in tracklist if (artist in t["artists"]) or (artist==None)]
	
	return {"list":ls}
	
@route("/artists")
def get_artists():
	
	return {"list":ARTISTS}
	
@route("/charts/artists")
def get_charts_artists():
	since = request.query.get("since")
	to = request.query.get("to")
	
	return {"list":db_aggregate(by="ARTIST",since=since,to=to)}
	
@route("/charts/tracks")
def get_charts_tracks():
	since = request.query.get("since")
	to = request.query.get("to")
	
	return {"list":db_aggregate(by="TRACK",since=since,to=to)}
	
@route("/charts")
def get_charts():
	since = request.query.get("since")
	to = request.query.get("to")
	
	return {"number":db_aggregate(since=since,to=to)}
	
@route("/pulse")
def get_pulse():
	since = request.query.get("since")
	to = request.query.get("to")
	(ts_start,ts_end) = getTimestamps(since,to)
	date_start = datetime.datetime.utcfromtimestamp(ts_start)
	date_end = datetime.datetime.utcfromtimestamp(ts_end)
	#date_start = datetime.datetime.utcfromtimestamp(min(timestamps))
	#date_end = datetime.datetime.utcnow()
	d_end = [date_end.year,date_end.month,date_end.day]
	
	step = request.query.get("step")
	if (step == None):
		step = "month"
	
	[step,stepn] = (step.split("-") + [1])[:2]	# makes the multiplier 1 if not assigned
	
	if step == "year":
		d_start = [date_start.year,1,1]
	elif step == "month":
		d_start = [date_start.year,date_start.month,1]
		
	inc = [i*int(stepn) for i in {"year":[1,0,0],"month":[0,1,0]}[step]]
	

	results = []
	
	d_current = d_start
	while True:
		d_current_end = addDate(d_current,inc)
		res = db_aggregate(since=d_current,to=d_current_end)
		results.append({"from":d_current,"to":d_current_end,"scrobbles":res})
		d_current = d_current_end
		if isPast(d_current_end,d_end):
			break
	
	return {"list":results}
		
	
@route("/top/artists")
def get_top_artists():
	since = request.query.get("since")
	to = request.query.get("to")
	(ts_start,ts_end) = getTimestamps(since,to)
	#date_start = datetime.datetime.utcfromtimestamp(ts_start)
	#date_end = datetime.datetime.utcfromtimestamp(ts_end)
	#d_end = [date_end.year,date_end.month,date_end.day]
	
	# We use a trailing multiplier instead of a separate argument for time and step to avoid weirdness
	# e.g. if our steps are weeks, but the time is a month, should the value for 3/31 go back to 2/28?
	step = request.query.get("step","month")	
	trail = int(request.query.get("trail","3"))
	
	[step,stepn] = (step.split("-") + [1])[:2]	# makes the multiplier 1 if not assigned
	#[time,timen] = (time.split("-") + [1])[:2]
	stepn = int(stepn)
	
	d_start = getStartOf(ts_start,step)
	d_end = getStartOf(ts_end,step)
	#if step == "year":
	#	d_start = [date_start.year,1,1]
	#elif step == "month":
	#	d_start = [date_start.year,date_start.month,1]
		
	#inc = [i*int(stepn) for i in {"year":[1,0,0],"month":[0,1,0]}[step]]
	#ran = [i*int(timen) for i in {"year":[1,0,0],"month":[0,1,0]}[time]]
	
	#d_start = addDate(d_start,inc)				# first range should end right after the first active scrobbling week / month / whatever relevant step
	#d_start = addDate(d_start,[-i for i in ran])		# go one range back to begin
	d_start = getNext(d_start,step,stepn)
	d_start = getNext(d_start,step,stepn * trail * -1)

	results = []
	
	d_current = d_start
	while True:
		d_current_end = getNext(d_current,step,stepn * trail)
		#print("Checking from " + str(d_current[0]) + "-" + str(d_current[1]) + "-" + str(d_current[2]) + " to " + str(d_current_end[0]) + "-" + str(d_current_end[1]) + "-" + str(d_current_end[2]))
		#d_current_end = addDate(d_current,ran)
		try:
			res = db_aggregate(since=d_current,to=d_current_end,by="ARTIST")[0]
			results.append({"from":d_current,"to":d_current_end,"artist":res["artist"],"scrobbles":res["scrobbles"]})
		except:
			results.append({"from":d_current,"to":d_current_end,"artist":None,"scrobbles":0})
		d_current = getNext(d_current,step,stepn)
		#d_current = addDate(d_current,inc)
		if isPast(d_current_end,d_end):
			break
	
	return {"list":results}


def getStartOf(timestamp,unit):
	date = datetime.datetime.utcfromtimestamp(timestamp)
	if unit == "year":
		return [date.year,1,1]
	elif unit == "month":
		return [date.year,date.month,1]
	elif unit == "day":
		return [date.year,date.month,date.day]
	elif unit == "week":
		change = (date.weekday() + 1) % 7
		d = datetime.timedelta(days=change)
		newdate = date - d
		return [newdate.year,newdate.month,newdate.day]
		
def getNext(time,unit,step=1):
	if unit == "year":
		return [time[0] + step,time[1],time[2]]
	elif unit == "month":
		result = [time[0],time[1] + step,time[2]]
		while result[1] > 12:
			result[1] -= 12
			result[0] += 1
		while result[1] < 1:
			result[1] += 12
			result[0] -= 1
		return result
	elif unit == "day":
		dt = datetime.datetime(time[0],time[1],time[2])
		d = datetime.timedelta(days=step)
		newdate = dt + d
		return [newdate.year,newdate.month,newdate.day]
		#eugh
	elif unit == "week":
		return getNext(time,"day",step * 7)
	
# DEPRECATED
def addDate(date,inc):
	newdate = [1,1,1]
	newdate[0] = date[0] + inc[0]
	newdate[1] = date[1] + inc[1]
	newdate[2] = date[2] + inc[2]
	while (newdate[1] > 12):
		newdate[1] -= 12
		newdate[0] += 1
	while (newdate[1] < 1):
		newdate[1] += 12
		newdate[0] -= 1
	
	return newdate
	
def isPast(date,limit):
	if not date[0] == limit[0]:
		return date[0] > limit[0]
	if not date[1] == limit[1]:
		return date[1] > limit[1]
	return (date[2] > limit[2])

@get("/newscrobble")
def pseudo_post_scrobble():
	keys = FormsDict.decode(request.query) # The Dal★Shabet handler
	artists = keys.get("artist")
	title = keys.get("title")
	try:
		time = int(keys.get("time"))
	except:
		time = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp())
	(artists,title) = c.fullclean(artists,title)

	## this is necessary for localhost testing
	response.set_header("Access-Control-Allow-Origin","*")
	
	createScrobble(artists,title,time)
	
	if (time - lastsync) > 3600:
		sync()
	
	return ""
	
@post("/newscrobble")
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
	(artists,title) = c.fullclean(artists,title)

	## this is necessary for localhost testing
	response.set_header("Access-Control-Allow-Origin","*")
	
	createScrobble(artists,title,time)
	
	if (time - lastsync) > 3600:
		sync()
	
	return ""
	
@route("/sync")
def abouttoshutdown():
	sync()
	#sys.exit()
	
	
####
## Server operation
####



# Starts the server
def runserver(DATABASE_PORT):
	global lastsync
	lastsync = time = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp())
	#reload()
	#buildh()
	build_db()
	sovereign.updateIDs(ARTISTS)

	loadAPIkeys()

	run(host='0.0.0.0', port=DATABASE_PORT, server='waitress')


def build_db():
	
	global SCROBBLES
	
	SCROBBLESNEW = []
	for t in SCROBBLES:
		if not t[2]:
			SCROBBLESNEW.append(t)

	SCROBBLES = SCROBBLESNEW
	
	for f in os.listdir("scrobbles/"):
		
		if not (".tsv" in f):
			continue
		
		logfile = open("scrobbles/" + f)
		for l in logfile:
			
			l = l.replace("\n","")
			data = l.split("\t")
			
			## saving album in the scrobbles is supported, but for now we don't use it. It shouldn't be a defining part of the track (same song from Album or EP), but derived information
			artists = data[1].split("␟")
			#album = data[3]
			title = data[2]
			time = int(data[0])
			
			readScrobble(artists,title,time)
			
	
	
		


# Saves all cached entries to disk			
def sync():
	for idx in range(len(SCROBBLES)):
		if not SCROBBLES[idx][2]:
			
			t = getScrobbleObject(SCROBBLES[idx])
			
			artistss = "␟".join(t["artists"])
			timestamp = datetime.date.fromtimestamp(t["time"])
			
			entry = "\t".join([str(t["time"]),artistss,t["title"]])
		
			monthfile = open("scrobbles/" + str(timestamp.year) + "_" + str(timestamp.month) + ".tsv","a")
			monthfile.write(entry)
			monthfile.write("\n")
			monthfile.close()
			
			SCROBBLES[idx] = (SCROBBLES[idx][0],SCROBBLES[idx][1],True)
			
	global lastsync
	lastsync = time = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp())
	print("Database saved to disk.")
			




####
## Database queries
####



# Queries the database			
def db_query(artist=None,track=None,since=None,to=None):
	(since, to) = getTimestamps(since,to)
	
	
	# this is not meant as a search function. we *can* query the db with a string, but it only works if it matches exactly (and title string simply picks the first track with that name)	
	if isinstance(artist, str):
		artist = ARTISTS.index(artist)
	if isinstance(track, str):
		track = TRACKS.index(track)
	
	return [getScrobbleObject(s) for s in SCROBBLES if (s[0] == track or track==None) and (artist in TRACKS[s[0]][0] or artist==None) and (since < s[1] < to)]
	# pointless to check for artist when track is checked because every track has a fixed set of artists, but it's more elegant this way

		
	#thingsweneed = ["artists","title","time"]
	#return [{key:t[key] for key in thingsweneed} for t in DATABASE if (artist in t["artists"] or artist==None) and (t["title"]==title or title==None) and (since < t["time"] < to)]
	

# Queries that... well... aggregate
def db_aggregate(by=None,since=None,to=None):
	(since, to) = getTimestamps(since,to)
	
	if (by=="ARTIST"):
		#this is probably a really bad idea
		#for a in ARTISTS:
		#	num = len(db_query(artist=a,since=since,to=to))
		#	
				
		# alright let's try for real
		charts = {}
		for s in [scr for scr in SCROBBLES if since < scr[1] < to]:
			artists = TRACKS[s[0]][0]
			for a in sovereign.getCreditedList(artists):
				# this either creates the new entry or increments the existing one
				charts[a] = charts.setdefault(a,0) + 1
				
		ls = [{"artist":getArtistObject(ARTISTS[a]),"scrobbles":charts[a]} for a in charts]
		return sorted(ls,key=lambda k:k["scrobbles"], reverse=True)
		
	elif (by=="TRACK"):
		charts = {}
		for s in [scr for scr in SCROBBLES if since < scr[1] < to]:
			track = s[0]
			# this either creates the new entry or increments the existing one
			charts[track] = charts.setdefault(track,0) + 1
				
		ls = [{"track":getTrackObject(TRACKS[t]),"scrobbles":charts[t]} for t in charts]
		return sorted(ls,key=lambda k:k["scrobbles"], reverse=True)
		
	else:
		return len([scr for scr in SCROBBLES if since < scr[1] < to])
	


# Search for strings
def db_search(query,type=None):
	if type=="ARTIST":
		results = []
		for a in ARTISTS:
			if query.lower() in a.lower():
				results.append(a)
	
	if type=="TRACK":
		results = []
		for t in TRACKS:
			if query.lower() in t[1].lower():
				results.append(t)
	
	return results


####
## Useful functions
####


# Takes user inputs like YYYY/MM and returns the timestamps. Returns timestamp if timestamp was already given.	
def getTimestamps(f,t):
	#(f,t) = inp
	if isinstance(f, str):
		f = [int(x) for x in f.split("/")]
		
	if isinstance(t, str):
		t = [int(x) for x in t.split("/")]
		
	
	# this step is done if either the input is a list or the first step was done (which creates a list)	
	if isinstance(f, list):
		date = [1970,1,1,0,0]
		date[:len(f)] = f
		f = int(datetime.datetime(date[0],date[1],date[2],date[3],date[4],tzinfo=datetime.timezone.utc).timestamp())
		
	if isinstance(t, list):
		date = [1970,1,1,0,0]
		date[:len(t)] = t
		t = int(datetime.datetime(date[0],date[1],date[2],date[3],date[4],tzinfo=datetime.timezone.utc).timestamp())
		
		
	if (f==None):
		f = min(timestamps)
	if (t==None):
		t = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).timestamp()
	
	return (f,t)
	

	
def getArtistId(nameorid):
	if isinstance(nameorid,int):
		return nameorid
	else:
		try:
			return ARTISTS.index(nameorid)
		except:
			return -1
			
			
