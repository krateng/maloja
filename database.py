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
clients = []

lastsync = 0


### symmetric keys are fine for now since we hopefully use HTTPS
def loadAPIkeys():
	global clients
	createTSV("clients/authenticated_machines.tsv")
	clients = parseTSV("clients/authenticated_machines.tsv","string","string")

def checkAPIkey(k):
	return (k in [k for [k,d] in clients])

def getScrobbleObject(o):
	track = getTrackObject(TRACKS[o[0]])
	return {"artists":track["artists"],"title":track["title"],"time":o[1]}
	
def getArtistObject(o):
	return o
	
def getTrackObject(o):
	artists = [getArtistObject(ARTISTS[a]) for a in o[0]]
	return {"artists":artists,"title":o[1]}


	
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
	
@route("/artistcharts")
def get_charts():
	since = request.query.get("since")
	to = request.query.get("to")
	
	return {"list":db_aggregate(by="ARTIST",since=since,to=to)}
	
@route("/trackcharts")
def get_charts():
	since = request.query.get("since")
	to = request.query.get("to")
	
	return {"list":db_aggregate(by="TRACK",since=since,to=to)}
	
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

# Starts the server
def runserver(DATABASE_PORT):
	global lastsync
	lastsync = time = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp())
	#reload()
	#buildh()
	build_db()

	loadAPIkeys()

	run(host='0.0.0.0', port=DATABASE_PORT, server='waitress')


def build_db():
	
	global SCROBBLES
	
	SCROBBLESNEW = []
	for t in SCROBBLES:
		if not t[2]:
			SCROBBLESNEW.append(t)

	SCROBBLES = SCROBBLESNEW
	
	for f in os.listdir("logs/"):
		
		if not (".tsv" in f):
			continue
		
		logfile = open("logs/" + f)
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
		
			monthfile = open("logs/" + str(timestamp.year) + "_" + str(timestamp.month) + ".tsv","a")
			monthfile.write(entry)
			monthfile.write("\n")
			monthfile.close()
			
			SCROBBLES[idx] = (SCROBBLES[idx][0],SCROBBLES[idx][1],True)
			
	global lastsync
	lastsync = time = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp())
	print("Database saved to disk.")
			

# Queries the database			
def db_query(artist=None,track=None,since=0,to=9999999999):
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
def db_aggregate(by,since=0,to=9999999999):
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
			for a in artists:
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
	

# Takes user inputs like YYYY/MM and returns the timestamps. Returns timestamp if timestamp was already given.	
def getTimestamps(f,t):
	#(f,t) = inp
	if isinstance(f, str):
		sdate = [int(x) for x in f.split("/")]
		date = [1970,1,1,0,0]
		date[:len(sdate)] = sdate
		f = int(datetime.datetime(date[0],date[1],date[2],date[3],date[4],tzinfo=datetime.timezone.utc).timestamp())
	if isinstance(t, str):
		sdate = [int(x) for x in t.split("/")]
		date = [1970,1,1,0,0]
		date[:len(sdate)] = sdate
		t = int(datetime.datetime(date[0],date[1],date[2],date[3],date[4],tzinfo=datetime.timezone.utc).timestamp())
		
	if (f==None):
		f = 0
	if (t==None):
		t = 9999999999
	
	return (f,t)
	
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
			
