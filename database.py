from bottle import route, run, template, static_file, request, response
from importlib.machinery import SourceFileLoader
import waitress
import os
import datetime

DATABASE = []

SCROBBLES = []	# Format: tuple(track_ref,timestamp,saved)
ARTISTS = []	# Format: artist
TRACKS = []	# Format: tuple(frozenset(artist_ref,...),title)


# by id
#def getScrobbleObject(o):
#	#return {"artists":getTrackObject(SCROBBLES[o][0])["artists"],"title":getTrackObject(SCROBBLES[o][0])["title"],"time":SCROBBLES[o][1],"saved":SCROBBLES[o][2]}
#	return {"artists":getTrackObject(SCROBBLES[o][0])["artists"],"title":getTrackObject(SCROBBLES[o][0])["title"],"time":SCROBBLES[o][1]}
#	
#def getArtistObject(o):
#	return ARTISTS[o]
#	
#def getTrackObject(o):
#	return {"artists":[getArtistObject(a) for a in TRACKS[o][0]],"title":TRACKS[o][1]}

# by object

def getScrobbleObject(o):
	#return {"artists":getTrackObject(SCROBBLES[o][0])["artists"],"title":getTrackObject(SCROBBLES[o][0])["title"],"time":SCROBBLES[o][1],"saved":SCROBBLES[o][2]}
	track = getTrackObject(TRACKS[o[0]])
	return {"artists":track["artists"],"title":track["title"],"time":o[1]}
	
def getArtistObject(o):
	return o
	
def getTrackObject(o):
	artists = [getArtistObject(ARTISTS[a]) for a in o[0]]
	return {"artists":artists,"title":o[1]}


	
def createScrobble(artists,title,time):	
	i = getTrackID(artists,title)	
	obj = (i,time,False)
	SCROBBLES.append(obj)

def readScrobble(artists,title,time):	
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
	r = db_query(artist=keys.get("artist"))
	#print(r)
	response.content_type = "application/json; charset=UTF-8"
	#response.charset = 'UTF-8'
	return {"list":r} ##json can't be a list apparently???

	#r = db_query(artist=keys.get("artist"))
	#text = ""
	#for e in r:
	#	entry = ""
	#	for a in e["artists"]:
	#		entry += a + "/"
	#	entry += "	" + e["title"] + "\n"
	#	text += entry
	#return text

@route("/tracks")
def get_tracks():
	artist = request.query.get("artist")
	
	global TRACKS
	
	
	# turn the tupel of frozensets into a jsonable object
	#tracklist = [{"artists":list(a[0]),"title":a[1]} for a in TRACKS]
	
	#ls = [t for t in tracklist if (artist in t["artists"]) or (artist==None)]
	
	
	### WHICH ONE IS FASTER
	import time
	
	# Option 1
	ls = [getTrackObject(t) for t in TRACKS if (artist in t[0]) or (artist==None)]
	
	# Option 2 is a bit more elegant but much slower
	#tracklist = [getTrackObject(t) for t in TRACKS]
	#ls = [t for t in tracklist if (artist in t["artists"]) or (artist==None)]
	
	return {"list":ls}
	
@route("/artists")
def get_artists():
	response.content_type = "application/json; charset=UTF-8"
	#response.charset = "utf-8"
	return {"list":ARTISTS}
	
@route("/charts")
def get_charts():
	since = request.query.get("since")
	to = request.query.get("to")
	
	#better do something here to sum up the totals on db level (before converting to dicts)
	
	#results = db_query(since=since,to=to)
	#return {"list":results}

# Starts the server
def runserver(DATABASE_PORT):
	
	#reload()
	#buildh()
	build_db()

	run(host='0.0.0.0', port=DATABASE_PORT, server='waitress')


def build_db():
	
	newscrobbles = [t for t in SCROBBLES if not t[2]]
	
	for f in os.listdir("logs/"):
		#print(f)
		
		if not (".csv" in f):
			continue
		
		logfile = open("logs/" + f)
		for l in logfile:
			
			l = l.replace("\n","")
			data = l.split(",")
			#print(l)
			
			
			## saving album in the scrobbles is supported, but for now we don't use it. It shouldn't be a defining part of the track (same song from Album or EP), but derived information
			artists = data[1].split("/")
			#album = data[3]
			title = data[2]
			time = int(data[0])
			
			readScrobble(artists,title,time)
			
			#DATABASE.append({"artists":artists,"title":title,"time":time,"saved":True})
	
		

# builds database of artists and tracks
# UNUSED as it is very resource-heavy, use buildh() instead
def build():
	global ARTISTS
	global TRACKS
	
	artistlist = []
	tracklist = []
	for t in DATABASE:
		for a in t["artists"]:
			if a in artistlist:
				continue
			artistlist.append(a)
		
		# first check if the title exists at all to quickly rule out most titles	
		if (t["title"] in [tr["title"] for tr in tracklist]):
			#only it same title actually exists do we need to check if the song is the same
			
			
			if not (set(t["artists"]) in [set(tr["artists"]) for tr in tracklist if tr["title"] == t["title"]]): #wut
				tracklist.append({"artists":t["artists"],"title":t["title"]})
			
			### ALRIGHT
			#foundexisting = False
			#for track in [tr for tr in tracklist if tr["title"] == t["title"]]: #wtf did I just write
			#	#print("Check duplicate: " + str(track) + " AND " + str(t))
			#	if (set(track["artists"]) == set(t["artists"])):
			#		foundexisting = True
			#		#print("MATCH!")
			#		break
			#	#else:
			#		#print("NO MATCH!")
			#		
			#if not foundexisting:
			#	tracklist.append({"artists":t["artists"],"title":t["title"]})
		else:
			tracklist.append({"artists":t["artists"],"title":t["title"]})
		
		
	ARTISTS = artistlist
	TRACKS = tracklist


# builds database of artists and tracks
# uses better data types to quickly find all unique tracks
# now also UNUSED since we build everything in one step with build_db()
def buildh():
	global ARTISTS
	global TRACKS
	
	artistset = set()
	trackset = set()
	for t in DATABASE:
		for a in t["artists"]:
			#if a not in artistset:
			artistset.add(a)
		
		# we list the tracks as tupels of frozenset(artists) and track
		# this way they're hashable and easily comparable, but we need to change them back after we have the list		
		#if ((frozenset(t["artists"]),t["title"])) not in trackset:
		trackset.add((frozenset(t["artists"]),t["title"]))
			
	print("Done, now converting back!")
	
	ARTISTS = list(artistset)
	#TRACKS = [{"artists":list(a[0]),"title":a[1]} for a in trackset]
	#actually lets only convert this once we need it, kinda makes sense to store it in the tuple frozenset form
	TRACKS = list(trackset)


# Rebuilds the database from disk, keeps cached entries	
# unused, this is now done in build_db()
def reload():
	newdb = [t for t in DATABASE if not t["saved"]]
	
	for f in os.listdir("logs/"):
		#print(f)
		
		if not (".csv" in f):
			continue
		
		logfile = open("logs/" + f)
		for l in logfile:
			
			l = l.replace("\n","")
			data = l.split(",")
			#print(l)
			
			
			## saving album in the scrobbles is supported, but for now we don't use it. It shouldn't be a defining part of the track (same song from Album or EP), but derived information
			artists = data[1].split("/")
			#album = data[3]
			title = data[2]
			time = int(data[0])
			
			DATABASE.append({"artists":artists,"title":title,"time":time,"saved":True})

# Saves all cached entries to disk			
def flush():
	for t in DATABASE:
		if not t["saved"]:
		
			artistss = "/".join(t["artists"])
			timestamp = datetime.date.fromtimestamp(t["time"])
			
			entry = ",".join([str(t["time"]),artistss,t["title"]])
		
			monthfile = open("logs/" + str(timestamp.year) + "_" + str(timestamp.month) + ".csv","a")
			monthfile.write(entry)
			monthfile.write("\n")
			monthfile.close()
			
			t["saved"] = True
			

# Queries the database			
def db_query(artist=None,track=None,since=0,to=9999999999):
	if isinstance(since, str):
		sdate = [int(x) for x in since.split("/")]
		date = [1970,1,1,0,0]
		date[:len(sdate)] = sdate
		since = int(datetime.datetime(date[0],date[1],date[2],date[3],date[4],tzinfo=datetime.timezone.utc).timestamp())
	if isinstance(to, str):
		sdate = [int(x) for x in to.split("/")]
		date = [1970,1,1,0,0]
		date[:len(sdate)] = sdate
		to = int(datetime.datetime(date[0],date[1],date[2],date[3],date[4],tzinfo=datetime.timezone.utc).timestamp())
	
	# this is not meant as a search function. we *can* query the db with a string, but it only works if it matches exactly (and title string simply picks the first track with that name)	
	if isinstance(artist, str):
		artist = ARTISTS.index(artist)
	if isinstance(track, str):
		track = TRACKS.index(track)
	
	return [getScrobbleObject(s) for s in SCROBBLES if (s[0] == track or track==None) and (artist in TRACKS[s[0]][0] or artist==None) and (since < s[1] < to)]
	# pointless to check for artist when track is checked because every track has a fixed set of artists, but it's more elegant this way

		
	#thingsweneed = ["artists","title","time"]
	#return [{key:t[key] for key in thingsweneed} for t in DATABASE if (artist in t["artists"] or artist==None) and (t["title"]==title or title==None) and (since < t["time"] < to)]
	
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
			
