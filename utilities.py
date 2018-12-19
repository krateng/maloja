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
	
def parseAllTSV(path,*args):
	
	import os
	
	result = []
	for f in os.listdir(path + "/"):
		
		if (".tsv" in f):
			
			result += parseTSV(path + "/" + f,*args)
			
	return result
	
def createTSV(filename):
	import os
	
	if not os.path.exists(filename):
		open(filename,"w").close()
		
### Logging
		
def log(msg):
	print(msg)
	# best function ever	
	

### Media info

def getArtistInfo(artist):
	import re
	import os
	import urllib
	import json
	import _thread
	
	
	filename = re.sub("[^a-zA-Z0-9]","",artist)
	filepath = "info/artists/" + filename
	filepath_cache = "info/artists_cache/" + filename
	
	# check if custom image exists
	if os.path.exists(filepath + ".png"):
		imgurl = "/" + filepath + ".png"
	elif os.path.exists(filepath + ".jpg"):
		imgurl = "/" + filepath + ".jpg"
	elif os.path.exists(filepath + ".jpeg"):
		imgurl = "/" + filepath + ".jpeg"
	
	#check if cached image exists	
	elif os.path.exists(filepath_cache + ".png"):
		imgurl = "/" + filepath_cache + ".png"
	elif os.path.exists(filepath_cache + ".jpg"):
		imgurl = "/" + filepath_cache + ".jpg"
	elif os.path.exists(filepath_cache + ".jpeg"):
		imgurl = "/" + filepath_cache + ".jpeg"
		
		
	# check if custom desc exists
	if os.path.exists(filepath + ".txt"):
		with open(filepath + ".txt","r") as descfile:
			desc = descfile.read().replace("\n","")
	
	#check if cached desc exists	
	elif os.path.exists(filepath_cache + ".txt"):
		with open(filepath_cache + ".txt","r") as descfile:
			desc = descfile.read().replace("\n","")
			
	try:
		return {"image":imgurl,"info":desc}
	except NameError:
		pass
	#is this pythonic?
	
	
	# if we neither have a custom image nor a cached version, we return the address from lastfm, but cache that image for later use	
	with open("apikey","r") as keyfile:
		apikey = keyfile.read().replace("\n","")
	
	
	try:	
		url = "https://ws.audioscrobbler.com/2.0/?method=artist.getinfo&artist=" + urllib.parse.quote(artist) + "&api_key=" + apikey + "&format=json"
		response = urllib.request.urlopen(url)
		lastfm_data = json.loads(response.read())
		try:
			imgurl
		except NameError:
			imgurl = lastfm_data["artist"]["image"][2]["#text"]
			if imgurl == "":
				imgurl = "/info/artists/default.jpg"
			else:
				_thread.start_new_thread(cacheImage,(imgurl,"info/artists_cache",filename))
		try:
			desc
		except NameError:
			desc = lastfm_data["artist"]["bio"]["summary"].split("(1) ")[-1]
			with open(filepath_cache + ".txt","w") as descfile:
				descfile.write(desc)
		# this feels so dirty
		
		
		return {"image":imgurl,"info":desc}
	except:
		return {"image":"/info/artists/default.jpg","info":"No information available"}
		
	
	
def cacheImage(url,path,filename):
	import urllib.request
	response = urllib.request.urlopen(url)
	target = path + "/" + filename + "." + response.info().get_content_subtype()	
	urllib.request.urlretrieve(url,target)
	
	
	
def getTimeDesc(timestamp):
	import datetime
	tim = datetime.datetime.utcfromtimestamp(timestamp)
	return tim.strftime("%d. %b %Y %I:%M %p")
