import re
import os
import hashlib
from threading import Thread
import pickle
import urllib
import datetime


### TSV files

def parseTSV(filename,*args):
	f = open(filename)
	
	result = []
	for l in [l for l in f if (not l.startswith("#")) and (not l.strip()=="")]:
		
		l = l.replace("\n","").split("#")[0]
		data = list(filter(None,l.split("\t"))) # Multiple tabs are okay, we don't accept empty fields unless trailing
		entry = [] * len(args)
		for i in range(len(args)):
			if args[i]=="list":
				try:
					entry.append(data[i].split("␟"))
				except:
					entry.append([])
			elif args[i]=="string":
				try:
					entry.append(data[i])
				except:
					entry.append("")
			elif args[i]=="int":
				try:
					entry.append(int(data[i]))
				except:
					entry.append(0)
			elif args[i]=="bool":
				try:
					entry.append((data[i].lower() in ["true","yes","1","y"]))
				except:
					entry.append(False)
				
		result.append(entry)
		
	f.close()
	return result
	
def checksumTSV(folder):
	
	sums = ""
	
	for f in os.listdir(folder + "/"):
		if (f.endswith(".tsv")):
			f = open(folder + "/" + f,"rb")
			sums += hashlib.md5(f.read()).hexdigest() + "\n"
			f.close()
			
	return sums
	
# returns whether checksums match and sets the checksum to invalid if they don't (or sets the new one if no previous one exists)
def combineChecksums(filename,checksums):
	import os
	
	if os.path.exists(filename + ".rulestate"):
		f = open(filename + ".rulestate","r")
		oldchecksums = f.read()
		f.close()
		if oldchecksums == checksums:
		# the new checksum given by the calling db server represents the rule state that all current unsaved scrobbles were created under
		# if this is the same as the existing one, we're all good
			return True
		elif (oldchecksums != "INVALID"):
			#if not, the file is not consistent to any single rule state (some scrobbles were created with an old ruleset, some not)
			f = open(filename + ".rulestate","w")
			f.write("INVALID") # this will never match any sha256sum
			f.close()
			return False
		else:
			#if the file already says invalid, no need to open it and rewrite
			return False
	else:
		f = open(filename + ".rulestate","w")
		f.write(checksums)
		f.close()
		return True
	
# checks ALL files for their rule state. if they are all the same as the current loaded one, the entire database can be assumed to be consistent with the current ruleset
# in any other case, get out
def consistentRulestate(folder,checksums):
	
	result = []
	for scrobblefile in os.listdir(folder + "/"):
		
		if (scrobblefile.endswith(".tsv")):
		
			try:
				f = open(folder + "/" + scrobblefile + ".rulestate","r")
				if f.read() != checksums:
					return False
			
			except:
				return False
			finally:
				f.close()
	
	return True
	
	
def parseAllTSV(path,*args):

	
	result = []
	for f in os.listdir(path + "/"):
		
		if (f.endswith(".tsv")):
			
			result += parseTSV(path + "/" + f,*args)
			
	return result
	
def createTSV(filename):

	if not os.path.exists(filename):
		open(filename,"w").close()

def addEntry(filename,a):

	createTSV(filename)
	
	line = "\t".join(a)
	with open(filename,"a") as f:
		f.write(line + "\n")

def addEntries(filename,al):
	
	with open(filename,"a") as f:
		for a in al:
			line = "\t".join(a)
			f.write(line + "\n")



### Useful functions

def int_or_none(input_):
	try:
		return int(input_)
	except:
		return None
		
def cleandict(d):
	newdict = {k:d[k] for k in d if d[k] is not None}
	d.clear()
	d.update(newdict)



		
		
### Logging
		
def log(msg):
	import inspect
	now = datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M:%S")
	module = inspect.getmodule(inspect.stack()[1][0]).__name__
	if module == "__main__": module = "mainserver"
	print("[" + module + "] " + msg)
	with open("logs/" + module + ".log","a") as logfile:
		logfile.write(now + "  " + msg + "\n")
	


### Media info

def apirequest(artists=None,artist=None,title=None):
	
	import urllib.parse, urllib.request
	import json
	
	try:
		with open("apikey","r") as keyfile:
			apikey = keyfile.read().replace("\n","")
			
		if apikey == "NONE": return {"image":None}
	except:
		return {"image":None}
	
	
	sites = [
		{
			"name":"lastfm",
			"artisturl":"https://ws.audioscrobbler.com/2.0/?method=artist.getinfo&artist={artist}&api_key=" + apikey + "&format=json",
			"trackurl":"https://ws.audioscrobbler.com/2.0/?method=track.getinfo&track={title}&artist={artist}&api_key=" + apikey + "&format=json",
			"result_artist_imgurl":lambda data:data["artist"]["image"][3]["#text"],
			"result_track_imgurl":lambda data:data["track"]["album"]["image"][3]["#text"]
			#"result_artist_desc":lambda data:data["artist"]["bio"]["summary"],
			#"result_track_desc":lambda data:None
		}
	]
	
	
	# TRACKS
	if title is not None:
		for s in sites:
			try:
				artiststr = urllib.parse.quote(", ".join(artists))
				titlestr = urllib.parse.quote(title)
				response = urllib.request.urlopen(s["trackurl"].format(artist=artiststr,title=titlestr))
				data = json.loads(response.read())
				if s["result_track_imgurl"](data) != "":
					return {"image":s["result_track_imgurl"](data)}
			except:
				pass
		
		if len(artists) == 1:
			#return {"image":apirequest(artist=artists[0])["image"]}
			return {"image":None}
				
		# try the same track with every single artist
		for a in artists:
			rec = apirequest(artists=[a],title=title)
			if rec["image"] is not None:
				return rec
				
		return {"image":None}
		
	# ARTISTS		
	else:
		for s in sites:
			try:
				response = urllib.request.urlopen(s["artisturl"].format(artist=urllib.parse.quote(artist)))
				data = json.loads(response.read())
				if s["result_artist_imgurl"](data) != "":
					return {"image":s["result_artist_imgurl"](data)}
			except:
				pass
		
		return {"image":None}

# I think I've only just understood modules
cachedTracks = {}
cachedArtists = {}

def saveCache():
	fl = open("images/cache","wb")
	stream = pickle.dumps((cachedTracks,cachedArtists))
	fl.write(stream)
	fl.close()
	
def loadCache():
	try:
		fl = open("images/cache","rb")
	except:
		return
		
	try:
		ob = pickle.loads(fl.read())
		global cachedTracks, cachedArtists
		(cachedTracks, cachedArtists) = ob
	finally:
		fl.close()

def getTrackInfo(artists,title,fast=False):

	obj = (frozenset(artists),title)
	filename = "-".join([re.sub("[^a-zA-Z0-9]","",artist) for artist in artists]) + "_" + re.sub("[^a-zA-Z0-9]","",title)
	if filename == "": filename = str(hash(obj))
	filepath = "images/tracks/" + filename
	
	# check if custom image exists
	if os.path.exists(filepath + ".png"):
		imgurl = "/" + filepath + ".png"
		return {"image":imgurl}
	elif os.path.exists(filepath + ".jpg"):
		imgurl = "/" + filepath + ".jpg"
		return {"image":imgurl}
	elif os.path.exists(filepath + ".jpeg"):
		imgurl = "/" + filepath + ".jpeg"
		return {"image":imgurl}
		
	try:
		return {"image":cachedTracks[(frozenset(artists),title)]}
	except:
		pass
		
	# fast request only retuns cached and local results, generates redirect link for rest
	if fast:
		return "/image?title=" + urllib.parse.quote(title) + "&" + "&".join(["artist=" + urllib.parse.quote(a) for a in artists])
	
	result = apirequest(artists=artists,title=title)
	if result.get("image") is not None:
		cachedTracks[(frozenset(artists),title)] = result["image"]
		return result
	else:
		result = getArtistInfo(artist=artists[0])
		#cachedTracks[(frozenset(artists),title)] = result["image"]
		return result
	
def getArtistInfo(artist,fast=False):
	
	obj = artist
	filename = re.sub("[^a-zA-Z0-9]","",artist)
	if filename == "": filename = str(hash(obj))
	filepath = "images/artists/" + filename
	#filepath_cache = "info/artists_cache/" + filename
	
	# check if custom image exists
	if os.path.exists(filepath + ".png"):
		imgurl = "/" + filepath + ".png"
		return {"image":imgurl}
	elif os.path.exists(filepath + ".jpg"):
		imgurl = "/" + filepath + ".jpg"
		return {"image":imgurl}
	elif os.path.exists(filepath + ".jpeg"):
		imgurl = "/" + filepath + ".jpeg"
		return {"image":imgurl}
	

	try:
		return {"image":cachedArtists[artist]}
	except:
		pass
		
	
		
	# fast request only retuns cached and local results, generates redirect link for rest
	if fast:
		return "/image?artist=" + urllib.parse.quote(artist)
		
	
	result = apirequest(artist=artist)
	if result.get("image") is not None:
		cachedArtists[artist] = result["image"]
		return result
	else:
		return {"image":""}

def getTracksInfo(trackobjectlist,fast=False):

	threads = []
	
	for track in trackobjectlist:
		t = Thread(target=getTrackInfo,args=(track["artists"],track["title"],),kwargs={"fast":fast})
		t.start()
		threads.append(t)
	
	for t in threads:
		t.join()
		
		
	return [getTrackInfo(t["artists"],t["title"]) for t in trackobjectlist]
	
def getArtistsInfo(artistlist,fast=False):
	
	threads = []
	
	for artist in artistlist:
		t = Thread(target=getArtistInfo,args=(artist,),kwargs={"fast":fast})
		t.start()
		threads.append(t)
	
	for t in threads:
		t.join()
	
	# async calls only cached results, now we need to get them	
	return [getArtistInfo(a) for a in artistlist]



# new way of serving images
# instead always generate a link locally, but redirect that on the fly
# this way the page can load faster and images will trickle in without having to resort to XHTTP requests

def resolveImage(artist=None,track=None):
	if track is not None:
		return getTrackInfo(track["artists"],track["title"])["image"]
	elif artist is not None:
		return getArtistInfo(artist)["image"]
		
