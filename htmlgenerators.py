import urllib
from bottle import FormsDict
import datetime


def artistLink(name):	
	return "<a href='/artist?artist=" + urllib.parse.quote(name) + "'>" + name + "</a>"
	
def artistLinks(artists):
	return ", ".join([artistLink(a) for a in artists])
	
#def trackLink(artists,title):
def trackLink(track):
	artists,title = track["artists"],track["title"]
	return "<a href='/track?title=" + urllib.parse.quote(title) + "&" + "&".join(["artist=" + urllib.parse.quote(a) for a in artists]) + "'>" + title + "</a>"
	
#def scrobblesTrackLink(artists,title,timekeys,amount=None,pixels=None):
def scrobblesTrackLink(track,timekeys,amount=None,percent=None):
	artists,title = track["artists"],track["title"]
	inner = str(amount) if amount is not None else "<div style='width:" + str(percent) + "%;'></div>"
	return "<a href='/scrobbles?" + "&".join(["artist=" + urllib.parse.quote(a) for a in artists]) + "&title=" + urllib.parse.quote(title) + "&" + keysToUrl(timekeys) + "'>" + inner + "</a>"
	
def scrobblesArtistLink(artist,timekeys,amount=None,percent=None,associated=False):
	inner = str(amount) if amount is not None else "<div style='width:" + str(percent) + "%;'></div>"
	askey = "&associated" if associated else ""
	return "<a href='/scrobbles?artist=" + urllib.parse.quote(artist) + "&" + keysToUrl(timekeys) + askey + "'>" + inner + "</a>"
	
def scrobblesLink(timekeys,amount=None,percent=None,artist=None,track=None,associated=False):
	if track is not None: return scrobblesTrackLink(track,timekeys,amount,percent)
	if artist is not None: return scrobblesArtistLink(artist,timekeys,amount,percent,associated)
	inner = str(amount) if amount is not None else "<div style='width:" + str(percent) + "%;'></div>"
	return "<a href='/scrobbles?" + keysToUrl(timekeys) + "'>" + inner + "</a>"

# necessary because urllib.parse.urlencode doesnt handle multidicts
def keysToUrl(*dicts):
	st = ""
	keys = removeIdentical(*dicts)
	for k in keys:
		values = keys.getall(k)
		st += "&".join([urllib.parse.urlencode({k:v},safe="/") for v in values])
		st += "&"
	return st
	
def removeIdentical(*dicts):
	#combine multiple dicts
	keys = FormsDict()
	for d in dicts:
		for k in d:
			try: #multidicts
				for v in d.getall(k):
					keys.append(k,v)
			except: #normaldicts
				v = d.get(k)
				keys.append(k,v)
	
	new = FormsDict()
	for k in keys:
		values = set(keys.getall(k))
		for v in values:
			new.append(k,v)
			
	return new
	
def getTimeDesc(timestamp,short=False):
	tim = datetime.datetime.utcfromtimestamp(timestamp)
	if short:
		now = datetime.datetime.now(tz=datetime.timezone.utc)
		difference = int(now.timestamp() - timestamp)
		
		if difference < 10: return "just now"
		if difference < 60: return str(difference) + " seconds ago"
		difference = int(difference/60)
		if difference < 60: return str(difference) + " minutes ago" if difference>1 else str(difference) + " minute ago"
		difference = int(difference/60)
		if difference < 24: return str(difference) + " hours ago" if difference>1 else str(difference) + " hour ago"
		difference = int(difference/24)
		if difference < 5: return tim.strftime("%A")
		if difference < 31: return str(difference) + " days ago" if difference>1 else str(difference) + " day ago"
		#if difference < 300 and tim.year == now.year: return tim.strftime("%B")
		#if difference < 300: return tim.strftime("%B %Y")
		
		return tim.strftime("%d. %B %Y")
	else:
		return tim.strftime("%d. %b %Y %I:%M %p")
		
def getRangeDesc(timeA,timeB,inclusiveB=True):
	# string to list
	if isinstance(timeA,str): timeA = timeA.split("/")
	if isinstance(timeB,str): timeB = timeB.split("/")
	
	# if lists, we have it potentially much easier:
	if isinstance(timeA,list) and isinstance(timeB,list):
		if timeA == timeB:
			date = [1970,1,1]
			date[:len(timeA)] = timeA
			dto = datetime.datetime(date[0],date[1],date[2],tzinfo=datetime.timezone.utc)
			if len(timeA) == 3:
				return dto.strftime("%d. %b %Y")
			if len(timeA) == 2:
				return dto.strftime("%B %Y")
			if len(timeA) == 1:
				return dto.strftime("%Y")
	
		from database import getTimestamps
		
		(timeA, timeB) = getTimestamps(since=timeA, to=timeB)
					
					
	return getTimeDesc(timeA) + " to " + getTimeDesc(timeB)
	


# finds out if we want an artist or a track
#def interpretURLKeys(keys):
#	if "title" in keys:
#		return {"track":{"artists":keys.getall("artist"),"title":keys.get("title")}}
#	if "artist" in keys:
#		return {"artist":keys.get("artist")}
#	
#	return {}
	
# alright this is the last one
# one ultimate method to rule them all
# one method to take html keys and convert them into internal keys
# it renames them, interprets what's being asked, removes duplicates
# it gets rid of multidicts
# it does fecking everything
# it's the best
# fantastic
def KeySplit(keys,forceTrack=False,forceArtist=False):

	# output:
	# 1	keys that define the filtered object like artist or track
	# 2	keys that define time limits of the whole thing
	# 3	keys that define interal time ranges
	# 4	keys that define amount limits

	# 1
	if "title" in keys and not forceArtist:
		resultkeys1 = {"track":{"artists":keys.getall("artist"),"title":keys.get("title")}}
	elif "artist" in keys and not forceTrack:
		resultkeys1 = {"artist":keys.get("artist")}
		if "associated" in keys: resultkeys1["associated"] = True
	else:
		resultkeys1 = {}
		
	# 2
	resultkeys2 = {}
	if "since" in keys: resultkeys2["since"] = keys.get("since")
	elif "from" in keys: resultkeys2["since"] = keys.get("from")
	elif "start" in keys: resultkeys2["since"] = keys.get("start")
	#
	if "to" in keys: resultkeys2["to"] = keys.get("to")
	elif "until" in keys: resultkeys2["to"] = keys.get("until")
	elif "end" in keys: resultkeys2["to"] = keys.get("end")
	#
	if "in" in keys: resultkeys2["within"] = keys.get("in")
	elif "within" in keys: resultkeys2["within"] = keys.get("within")
	elif "during" in keys: resultkeys2["within"] = keys.get("during")
	
	
	#3
	resultkeys3 = {}
	if "step" in keys: [resultkeys3["step"],resultkeys3["stepn"]] = (keys["step"].split("-") + [1])[:2]
	if "stepn" in keys: resultkeys3["stepn"] = keys["stepn"] #overwrite if explicitly given
	if "stepn" in resultkeys3: resultkeys3["stepn"] = int(resultkeys3["stepn"]) #in both cases, convert it here
	if "trail" in keys: resultkeys3["trail"] = int(keys["trail"])
	
	
	#4
	resultkeys4 = {}
	if "max" in keys: resultkeys4["max_"] = int(keys["max"])
	
	return resultkeys1, resultkeys2, resultkeys3, resultkeys4

	
# limit a multidict to only the specified keys
# would be a simple constructor expression, but multidicts apparently don't let me do that
def pickKeys(d,*keys):
	if isinstance(d,dict):
		return {k:d.get(k) for k in d if k in keys}
	else:
		# create a normal dictionary of lists
		newd = {k:d.getall(k) for k in d if k in keys}
		# one by one add the list entries to the formsdict
		finald = FormsDict()
		for k in newd:
			for v in newd.get(k):
				finald.append(k,v)
				
		return finald

# removes all duplicate keys, except artists when a title is specified		
def clean(d):
	if isinstance(d,dict):
		return
	else:
		for k in d:
			if (k != "artist") or "title" not in d:
				d[k] = d.pop(k)
