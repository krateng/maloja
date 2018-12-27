


def artistLink(name):
	import urllib
	return "<a href='/artist?artist=" + urllib.parse.quote(name) + "'>" + name + "</a>"
	
def artistLinks(artists):
	return ", ".join([artistLink(a) for a in artists])
	
#def trackLink(artists,title):
def trackLink(track):
	artists,title = track["artists"],track["title"]
	import urllib
	return "<a href='/track?title=" + urllib.parse.quote(title) + "&" + "&".join(["artist=" + urllib.parse.quote(a) for a in artists]) + "'>" + title + "</a>"
	
#def scrobblesTrackLink(artists,title,timekeys,amount=None,pixels=None):
def scrobblesTrackLink(track,timekeys,amount=None,percent=None):
	artists,title = track["artists"],track["title"]
	import urllib
	inner = str(amount) if amount is not None else "<div style='width:" + str(percent) + "%;'></div>"
	return "<a href='/scrobbles?" + "&".join(["artist=" + urllib.parse.quote(a) for a in artists]) + "&title=" + urllib.parse.quote(title) + "&" + keysToUrl(timekeys) + "'>" + inner + "</a>"
	
def scrobblesArtistLink(artist,timekeys,amount=None,percent=None,associated=False):
	import urllib
	inner = str(amount) if amount is not None else "<div style='width:" + str(percent) + "%;'></div>"
	askey = "&associated" if associated else ""
	return "<a href='/scrobbles?artist=" + urllib.parse.quote(artist) + "&" + keysToUrl(timekeys) + askey + "'>" + inner + "</a>"

# necessary because urllib.parse.urlencode doesnt handle multidicts
def keysToUrl(*dicts):
	import urllib
	st = ""
	keys = removeIdentical(*dicts)
	for k in keys:
		values = keys.getall(k)
		st += "&".join([urllib.parse.urlencode({k:v},safe="/") for v in values])
		st += "&"
	return st
	
def removeIdentical(*dicts):
	from bottle import FormsDict
	
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
	
def getTimeDesc(timestamp):
	import datetime
	tim = datetime.datetime.utcfromtimestamp(timestamp)
	return tim.strftime("%d. %b %Y %I:%M %p")
	
	
# limit a multidict to only the specified keys
# would be a simple constructor expression, but multidicts apparently don't let me do that
def pickKeys(d,*keys):
	from bottle import FormsDict
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
	from bottle import FormsDict
	if isinstance(d,dict):
		return
	else:
		for k in d:
			if (k != "artist") or "title" not in d:
				d[k] = d.pop(k)
