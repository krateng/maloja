from bottle import route, run, template, static_file, request, response
from importlib.machinery import SourceFileLoader
import waitress
import os
import datetime

DATABASE = []

ARTISTS = []
TRACKS = []


@route("/scrobbles")
def get_scrobbles():
	keys = request.query
	r = db_query(artist=keys.get("artist"))
	#print(r)
	response.content_type = "application/json"
	return {"object":r} ##json can't be a list apparently???

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
	
	ls = [t for t in TRACKS if (artist in t["artists"])]
	return {"object":ls}

# Starts the server
def runserver(DATABASE_PORT):
	
	reload()
	buildh()

	run(host='0.0.0.0', port=DATABASE_PORT, server='waitress')
	

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
					
			#if not foundexisting:
			#	tracklist.append({"artists":t["artists"],"title":t["title"]})
		else:
			tracklist.append({"artists":t["artists"],"title":t["title"]})
		
		
	ARTISTS = artistlist
	TRACKS = tracklist


# builds database of artists and tracks
# uses better data types to quickly find all unique tracks
def buildh():
	global ARTISTS
	global TRACKS
	
	artistset = set()
	trackset = set()
	for t in DATABASE:
		for a in t["artists"]:
			if a not in artistset:
				artistset.add(a)
		
		# we list the tracks as tupels of frozenset(artists) and track
		# this way they're hashable and easily comparable, but we need to change them back after we have the list		
		if ((frozenset(t["artists"]),t["title"])) not in trackset:
			trackset.add((frozenset(t["artists"]),t["title"]))
			
	print("Done, now converting back!")
	
	ARTISTS = list(artistset)
	TRACKS = [{"artists":list(a[0]),"title":a[1]} for a in trackset]

# Rebuilds the database from disk, keeps cached entries	
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
def db_query(artist=None,title=None,since=0,to=9999999999):
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
		
	thingsweneed = ["artists","title","time"]
	return [{key:t[key] for key in thingsweneed} for t in DATABASE if (artist in t["artists"] or artist==None) and (t["title"]==title or title==None) and (since < t["time"] < to)]
	
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
			
