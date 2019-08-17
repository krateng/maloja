import re
import os
import hashlib
from threading import Thread, Timer
import pickle
import json
import urllib
import datetime
import random
import itertools
from doreah import settings
from doreah import caching
from doreah.logging import log
from doreah.regular import yearly, daily

from external import api_request_track, api_request_artist



#####
## SERIALIZE
#####

def serialize(obj):
	try:
		return json.dumps(obj)
	except:
		if isinstance(obj,list) or isinstance(obj,tuple):
			return "[" + ",".join(serialize(o) for o in obj) + "]"
		elif isinstance(obj,dict):
			return "{" + ",".join(serialize(o) + ":" + serialize(obj[o]) for o in obj) + "}"
		return json.dumps(obj.hashable())


	#if isinstance(obj,list) or if isinstance(obj,tuple):
	#	return "[" + ",".join(dumps(o) for o in obj) + "]"
	#if isinstance(obj,str)







#####
## RULESTATE VALIDATION
#####





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













#####
## IMAGES
#####









### Caches

cacheage = settings.get_settings("CACHE_EXPIRE_POSITIVE") * 24 * 3600
cacheage_neg = settings.get_settings("CACHE_EXPIRE_NEGATIVE") * 24 * 3600

artist_cache = caching.Cache(name="imgcache_artists",maxage=cacheage,maxage_negative=cacheage_neg,persistent=True)
track_cache = caching.Cache(name="imgcache_tracks",maxage=cacheage,maxage_negative=cacheage_neg,persistent=True)


# removes emojis and weird shit from names
def clean(name):
	return "".join(c for c in name if c.isalnum() or c in []).strip()

def local_files(artist=None,artists=None,title=None):

	# check if we're dealing with a track or artist, then clean up names
	# (only remove non-alphanumeric, allow korean and stuff)
	if title is not None and artists is not None:
		track = True
		title, artists = clean(title), [clean(a) for a in artists]
	elif artist is not None:
		track = False
		artist = clean(artist)
	else: return []


	superfolder = "images/tracks/" if track else "images/artists/"

	filenames = []

	if track:
		#unsafeartists = [artist.translate(None,"-_./\\") for artist in artists]
		safeartists = [re.sub("[^a-zA-Z0-9]","",artist) for artist in artists]
		#unsafetitle = title.translate(None,"-_./\\")
		safetitle = re.sub("[^a-zA-Z0-9]","",title)

		if len(artists) < 4:
			unsafeperms = itertools.permutations(artists)
			safeperms = itertools.permutations(safeartists)
		else:
			unsafeperms = [sorted(artists)]
			safeperms = [sorted(safeartists)]


		for unsafeartistlist in unsafeperms:
			filename = "-".join(unsafeartistlist) + "_" + title
			if filename != "":
				filenames.append(filename)
				filenames.append(filename.lower())
		for safeartistlist in safeperms:
			filename = "-".join(safeartistlist) + "_" + safetitle
			if filename != "":
				filenames.append(filename)
				filenames.append(filename.lower())
		filenames = list(set(filenames))
		if len(filenames) == 0: filenames.append(str(hash((frozenset(artists),title))))
	else:
		#unsafeartist = artist.translate(None,"-_./\\")
		safeartist = re.sub("[^a-zA-Z0-9]","",artist)

		filename = artist
		if filename != "":
			filenames.append(filename)
			filenames.append(filename.lower())
		filename = safeartist
		if filename != "":
			filenames.append(filename)
			filenames.append(filename.lower())

		filenames = list(set(filenames))
		if len(filenames) == 0: filenames.append(str(hash(artist)))

	images = []

	for purename in filenames:
		# direct files
		for ext in ["png","jpg","jpeg","gif"]:
			#for num in [""] + [str(n) for n in range(0,10)]:
			if os.path.exists(superfolder + purename + "." + ext):
				images.append("/" + superfolder + purename + "." + ext)

		# folder
		try:
			for f in os.listdir(superfolder + purename + "/"):
				if f.split(".")[-1] in ["png","jpg","jpeg","gif"]:
					images.append("/" + superfolder + purename + "/" + f)
		except:
			pass

	return images



# these caches are there so we don't check all files every time, but return the same one
local_cache_age = settings.get_settings("LOCAL_IMAGE_ROTATE")
local_artist_cache = caching.Cache(maxage=local_cache_age)
local_track_cache = caching.Cache(maxage=local_cache_age)

def getTrackImage(artists,title,fast=False):

#	obj = (frozenset(artists),title)
#	filename = "-".join([re.sub("[^a-zA-Z0-9]","",artist) for artist in sorted(artists)]) + "_" + re.sub("[^a-zA-Z0-9]","",title)
#	if filename == "": filename = str(hash(obj))
#	filepath = "images/tracks/" + filename

	if settings.get_settings("USE_LOCAL_IMAGES"):

		try:
			return local_track_cache.get((frozenset(artists),title))
		except:
			images = local_files(artists=artists,title=title)
			if len(images) != 0:
				#return random.choice(images)
				res = random.choice(images)
				local_track_cache.add((frozenset(artists),title),res)
				return urllib.parse.quote(res)


	# check if custom image exists
#	if os.path.exists(filepath + ".png"):
#		imgurl = "/" + filepath + ".png"
#		return imgurl
#	elif os.path.exists(filepath + ".jpg"):
#		imgurl = "/" + filepath + ".jpg"
#		return imgurl
#	elif os.path.exists(filepath + ".jpeg"):
#		imgurl = "/" + filepath + ".jpeg"
#		return imgurl
#	elif os.path.exists(filepath + ".gif"):
#		imgurl = "/" + filepath + ".gif"
#		return imgurl


	try:
		# check our cache
		# if we have cached the nonexistence of that image, we immediately return the redirect to the artist and let the resolver handle it
		# (even if we're not in a fast lookup right now)
		#result = cachedTracks[(frozenset(artists),title)]
		result = track_cache.get((frozenset(artists),title)) #track_from_cache(artists,title)
		if result is not None: return result
		else:
			for a in artists:
				res = getArtistImage(artist=a,fast=True)
				if res != "": return res
			return ""
	except:
		pass

	# do we have an api key?
#	apikey = settings.get_settings("LASTFM_API_KEY")
#	if apikey is None: return "" # DO NOT CACHE THAT


	# fast request only retuns cached and local results, generates redirect link for rest
	if fast: return "/image?title=" + urllib.parse.quote(title) + "&" + "&".join(["artist=" + urllib.parse.quote(a) for a in artists])

	# non-fast lookup (esentially only the resolver lookup)
	result = api_request_track((artists,title))

	# cache results (even negative ones)
	#cachedTracks[(frozenset(artists),title)] = result
	track_cache.add((frozenset(artists),title),result) #cache_track(artists,title,result)

	# return either result or redirect to artist
	if result is not None: return result
	else:
		for a in artists:
			res = getArtistImage(artist=a,fast=False)
			if res != "": return res
		return ""


def getArtistImage(artist,fast=False):

#	obj = artist
#	filename = re.sub("[^a-zA-Z0-9]","",artist)
#	if filename == "": filename = str(hash(obj))
#	filepath = "images/artists/" + filename
#	#filepath_cache = "info/artists_cache/" + filename

	if settings.get_settings("USE_LOCAL_IMAGES"):

		try:
			return local_artist_cache.get(artist)
		except:
			images = local_files(artist=artist)
			if len(images) != 0:
				#return random.choice(images)
				res = random.choice(images)
				local_artist_cache.add(artist,res)
				return urllib.parse.quote(res)


	# check if custom image exists
#	if os.path.exists(filepath + ".png"):
#		imgurl = "/" + filepath + ".png"
#		return imgurl
#	elif os.path.exists(filepath + ".jpg"):
#		imgurl = "/" + filepath + ".jpg"
#		return imgurl
#	elif os.path.exists(filepath + ".jpeg"):
#		imgurl = "/" + filepath + ".jpeg"
#		return imgurl
#	elif os.path.exists(filepath + ".gif"):
#		imgurl = "/" + filepath + ".gif"
#		return imgurl


	try:
		#result = cachedArtists[artist]
		result = artist_cache.get(artist) #artist_from_cache(artist)
		if result is not None: return result
		else: return ""
	except:
		pass



	# do we have an api key?
#	apikey = settings.get_settings("LASTFM_API_KEY")
#	if apikey is None: return "" # DO NOT CACHE THAT



	# fast request only retuns cached and local results, generates redirect link for rest
	if fast: return "/image?artist=" + urllib.parse.quote(artist)

	# non-fast lookup (esentially only the resolver lookup)
	result = api_request_artist(artist=artist)

	# cache results (even negative ones)
	#cachedArtists[artist] = result
	artist_cache.add(artist,result) #cache_artist(artist,result)

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


















#####
## PULSE MAINTENANCE
#####



@yearly
def update_medals():


	from database import MEDALS, MEDALS_TRACKS, STAMPS, get_charts_artists, get_charts_tracks

	currentyear = datetime.datetime.utcnow().year
	try:
		firstyear = datetime.datetime.utcfromtimestamp(STAMPS[0]).year
	except:
		firstyear = currentyear


	MEDALS.clear()
	for year in range(firstyear,currentyear):

		charts = get_charts_artists(within=[year])
		for a in charts:

			artist = a["artist"]
			if a["rank"] == 1: MEDALS.setdefault(artist,{}).setdefault("gold",[]).append(year)
			elif a["rank"] == 2: MEDALS.setdefault(artist,{}).setdefault("silver",[]).append(year)
			elif a["rank"] == 3: MEDALS.setdefault(artist,{}).setdefault("bronze",[]).append(year)
			else: break

	MEDALS_TRACKS.clear()
	for year in range(firstyear,currentyear):

		charts = get_charts_tracks(within=[year])
		for t in charts:

			track = (frozenset(t["track"]["artists"]),t["track"]["title"])
			if t["rank"] == 1: MEDALS_TRACKS.setdefault(track,{}).setdefault("gold",[]).append(year)
			elif t["rank"] == 2: MEDALS_TRACKS.setdefault(track,{}).setdefault("silver",[]).append(year)
			elif t["rank"] == 3: MEDALS_TRACKS.setdefault(track,{}).setdefault("bronze",[]).append(year)
			else: break

@daily
def update_weekly():

	from database import WEEKLY_TOPTRACKS, WEEKLY_TOPARTISTS, get_charts_artists, get_charts_tracks
	from malojatime import ranges, thisweek


	WEEKLY_TOPARTISTS.clear()
	WEEKLY_TOPTRACKS.clear()

	for week in ranges(step="week"):
		if week == thisweek(): break
		for a in get_charts_artists(timerange=week):
			artist = a["artist"]
			if a["rank"] == 1: WEEKLY_TOPARTISTS[artist] = WEEKLY_TOPARTISTS.setdefault(artist,0) + 1

		for t in get_charts_tracks(timerange=week):
			track = (frozenset(t["track"]["artists"]),t["track"]["title"])
			if t["rank"] == 1: WEEKLY_TOPTRACKS[track] = WEEKLY_TOPTRACKS.setdefault(track,0) + 1
