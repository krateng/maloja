import re
import os
import hashlib
from threading import Thread
import pickle
import urllib
import datetime
from doreah import settings


### TSV files

def parseTSV(filename,*args,escape=True):
	f = open(filename)

	result = []
	for l in [l for l in f if (not l.startswith("#")) and (not l.strip()=="")]:

		l = l.replace("\n","")
		if escape:
			l = l.split("#")[0]
		l = l.replace(r"\num","#") # translate escape sequences even if we don't support comments in the file and they are not actually necessary (they might still be used for some reason)
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


def parseAllTSV(path,*args,escape=True):


	result = []
	for f in os.listdir(path + "/"):

		if (f.endswith(".tsv")):

			result += parseTSV(path + "/" + f,*args,escape=escape)

	return result

def createTSV(filename):

	if not os.path.exists(filename):
		open(filename,"w").close()

def addEntry(filename,a,escape=True):

	createTSV(filename)

	line = "\t".join(a)
	if escape: line = line.replace("#",r"\num")
	with open(filename,"a") as f:
		f.write(line + "\n")

def addEntries(filename,al,escape=True):

	with open(filename,"a") as f:
		for a in al:
			line = "\t".join(a)
			if escape: line = line.replace("#",r"\num")
			f.write(line + "\n")



### Useful functions

#def int_or_none(input_):
#	try:
#		return int(input_)
#	except:
#		return None

#def cleandict(d):
#	newdict = {k:d[k] for k in d if d[k] is not None}
#	d.clear()
#	d.update(newdict)





### Logging
# now handled by doreah

#def log(msg,module=None):
#	now = datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M:%S")
#	if module is None:
#		import inspect
#		module = inspect.getmodule(inspect.stack()[1][0]).__name__
#		if module == "__main__": module = "mainserver"
#	print("[" + module + "] " + msg)
#	with open("logs/" + module + ".log","a") as logfile:
#		logfile.write(now + "  " + msg + "\n")


### not meant to be precise, just for a rough idea
# now handled by doreah
#measurement = 0
#def clock(*args):
#	import time
#	global measurement
#	now = time.time()
#	if len(args) > 0:
#		print(args[0] + ": " + str(now - measurement))
#	measurement = now




### Media info

def apirequest(artists=None,artist=None,title=None):

	import urllib.parse, urllib.request
	import json

	#try:
		#with open("apikey","r") as keyfile:
		#	apikey = keyfile.read().replace("\n","")

	apikey = settings.get_settings("LASTFM_API_KEY")
	if apikey is None: return None
	#except:
	#	return None


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
				log("API: " + s["name"] + "; Image request: " + "/".join(artists) + " - " + title,module="external")
				data = json.loads(response.read())
				if s["result_track_imgurl"](data) != "":
					return s["result_track_imgurl"](data)
			except:
				pass

		if len(artists) == 1:
			#return {"image":apirequest(artist=artists[0])["image"]}
			return None

		# try the same track with every single artist
		for a in artists:
			rec = apirequest(artists=[a],title=title)
			if rec is not None:
				return rec

		return None

	# ARTISTS
	else:
		for s in sites:
			try:
				response = urllib.request.urlopen(s["artisturl"].format(artist=urllib.parse.quote(artist)))
				log("API: " + s["name"] + "; Image request: " + artist,module="external")
				data = json.loads(response.read())
				if s["result_artist_imgurl"](data) != "":
					return s["result_artist_imgurl"](data)
			except:
				pass

		return None

# I think I've only just understood modules
cachedTracks = {}
cachedArtists = {}

cachedTracksDays = {}
cachedArtistsDays = {}

def cache_track(artists,title,result):
	cachedTracks[(frozenset(artists),title)] = result
	day = datetime.date.today().toordinal()
	cachedTracksDays[(frozenset(artists),title)] = day
def cache_artist(artist,result):
	cachedArtists[artist] = result
	day = datetime.date.today().toordinal()
	cachedArtistsDays[artist] = day

def track_from_cache(artists,title):
	try:
		res = cachedTracks[(frozenset(artists),title)]
	except:
		# no entry there, let the calling function know
		raise KeyError()

	if res is None:
		retain = settings.get_settings("CACHE_EXPIRE_NEGATIVE")
	else:
		retain = settings.get_settings("CACHE_EXPIRE_POSITIVE")

	# if the settings say caches never expire, just return
	if retain is None: return res

	# look if entry is too old
	nowday = datetime.date.today().toordinal()
	cacheday = cachedTracksDays[(frozenset(artists),title)]

	if (nowday - cacheday) > retain:
		# fetch the new image in the background, but still return the old one for one last time
		log("Expired cache for " + "/".join(artists) + " - " + title)
		del cachedTracks[(frozenset(artists),title)]
		t = Thread(target=getTrackImage,args=(artists,title,))
		t.start()
	return res

def artist_from_cache(artist):
	try:
		res = cachedArtists[artist]
	except:
		# no entry there, let the calling function know
		raise KeyError()

	if res is None:
		retain = settings.get_settings("CACHE_EXPIRE_NEGATIVE")
	else:
		retain = settings.get_settings("CACHE_EXPIRE_POSITIVE")

	# if the settings say caches never expire, just return
	if retain is None: return res

	# look if entry is too old
	nowday = datetime.date.today().toordinal()
	cacheday = cachedArtistsDays[artist]

	if (nowday - cacheday) > retain:
		# fetch the new image in the background, but still return the old one for one last time
		log("Expired cache for " + artist)
		del cachedArtists[artist]
		t = Thread(target=getArtistImage,args=(artist,))
		t.start()
	return res


def saveCache():
	fl = open("images/cache","wb")
	stream = pickle.dumps({"tracks":cachedTracks,"artists":cachedArtists,"tracks_days":cachedTracksDays,"artists_days":cachedArtistsDays})
	fl.write(stream)
	fl.close()

def loadCache():
	try:
		fl = open("images/cache","rb")
	except:
		return

	try:
		ob = pickle.loads(fl.read())
		global cachedTracks, cachedArtists, cachedTracksDays, cachedArtistsDays
		cachedTracks, cachedArtists, cachedTracksDays, cachedArtistsDays = ob["tracks"],ob["artists"],ob["tracks_days"],ob["artists_days"]
		#(cachedTracks, cachedArtists) = ob
	finally:
		fl.close()

	# remove corrupt caching from previous versions
	toremove = []
	for k in cachedTracks:
		if cachedTracks[k] == "":
			toremove.append(k)
	for k in toremove:
		del cachedTracks[k]
		log("Removed invalid cache key: " + str(k))

	toremove = []
	for k in cachedArtists:
		if cachedArtists[k] == "":
			toremove.append(k)
	for k in toremove:
		del cachedArtists[k]
		log("Removed invalid cache key: " + str(k))

def getTrackImage(artists,title,fast=False):

	obj = (frozenset(artists),title)
	filename = "-".join([re.sub("[^a-zA-Z0-9]","",artist) for artist in artists]) + "_" + re.sub("[^a-zA-Z0-9]","",title)
	if filename == "": filename = str(hash(obj))
	filepath = "images/tracks/" + filename

	# check if custom image exists
	if os.path.exists(filepath + ".png"):
		imgurl = "/" + filepath + ".png"
		return imgurl
	elif os.path.exists(filepath + ".jpg"):
		imgurl = "/" + filepath + ".jpg"
		return imgurl
	elif os.path.exists(filepath + ".jpeg"):
		imgurl = "/" + filepath + ".jpeg"
		return imgurl
	elif os.path.exists(filepath + ".gif"):
		imgurl = "/" + filepath + ".gif"
		return imgurl


	try:
		# check our cache
		# if we have cached the nonexistence of that image, we immediately return the redirect to the artist and let the resolver handle it
		# (even if we're not in a fast lookup right now)
		#result = cachedTracks[(frozenset(artists),title)]
		result = track_from_cache(artists,title)
		if result is not None: return result
		else:
			for a in artists:
				res = getArtistImage(artist=a,fast=True)
				if res != "": return res
			return ""
	except:
		pass

	# do we have an api key?
	apikey = settings.get_settings("LASTFM_API_KEY")
	if apikey is None: return "" # DO NOT CACHE THAT


	# fast request only retuns cached and local results, generates redirect link for rest
	if fast: return "/image?title=" + urllib.parse.quote(title) + "&" + "&".join(["artist=" + urllib.parse.quote(a) for a in artists])

	# non-fast lookup (esentially only the resolver lookup)
	result = apirequest(artists=artists,title=title)

	# cache results (even negative ones)
	#cachedTracks[(frozenset(artists),title)] = result
	cache_track(artists,title,result)

	# return either result or redirect to artist
	if result is not None: return result
	else:
		for a in artists:
			res = getArtistImage(artist=a,fast=False)
			if res != "": return res
		return ""



def getArtistImage(artist,fast=False):

	obj = artist
	filename = re.sub("[^a-zA-Z0-9]","",artist)
	if filename == "": filename = str(hash(obj))
	filepath = "images/artists/" + filename
	#filepath_cache = "info/artists_cache/" + filename

	# check if custom image exists
	if os.path.exists(filepath + ".png"):
		imgurl = "/" + filepath + ".png"
		return imgurl
	elif os.path.exists(filepath + ".jpg"):
		imgurl = "/" + filepath + ".jpg"
		return imgurl
	elif os.path.exists(filepath + ".jpeg"):
		imgurl = "/" + filepath + ".jpeg"
		return imgurl
	elif os.path.exists(filepath + ".gif"):
		imgurl = "/" + filepath + ".gif"
		return imgurl


	try:
		#result = cachedArtists[artist]
		result = artist_from_cache(artist)
		if result is not None: return result
		else: return ""
	except:
		pass



	# do we have an api key?
	apikey = settings.get_settings("LASTFM_API_KEY")
	if apikey is None: return "" # DO NOT CACHE THAT



	# fast request only retuns cached and local results, generates redirect link for rest
	if fast: return "/image?artist=" + urllib.parse.quote(artist)

	# non-fast lookup (esentially only the resolver lookup)
	result = apirequest(artist=artist)

	# cache results (even negative ones)
	#cachedArtists[artist] = result
	cache_artist(artist,result)

	if result is not None: return result
	else: return ""

def getTrackImages(trackobjectlist,fast=False):

	threads = []

	for track in trackobjectlist:
		t = Thread(target=getTrackImage,args=(track["artists"],track["title"],),kwargs={"fast":fast})
		t.start()
		threads.append(t)

	for t in threads:
		t.join()


	return [getTrackImage(t["artists"],t["title"]) for t in trackobjectlist]

def getArtistImages(artistlist,fast=False):

	threads = []

	for artist in artistlist:
		t = Thread(target=getArtistImage,args=(artist,),kwargs={"fast":fast})
		t.start()
		threads.append(t)

	for t in threads:
		t.join()

	# async calls only cached results, now we need to get them
	return [getArtistImage(a) for a in artistlist]



# new way of serving images
# instead always generate a link locally, but redirect that on the fly
# this way the page can load faster and images will trickle in without having to resort to XHTTP requests

def resolveImage(artist=None,track=None):
	if track is not None:
		return getTrackImage(track["artists"],track["title"])
	elif artist is not None:
		return getArtistImage(artist)
