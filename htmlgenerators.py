


def artistLink(name):
	import urllib
	return "<a href='/artist?artist=" + urllib.parse.quote(name) + "'>" + name + "</a>"

# necessary because urllib.parse.urlencode doesnt handle multidicts
def keysToUrl(*dicts):
	import urllib
	st = ""
	keys = removeIdentical(*dicts)
	for k in keys:
		values = keys.getall(k)
		st += "&".join([urllib.parse.urlencode({k:v}) for v in values])
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
# hardcoding this to only allow multi values for a key in one case: artist when there is also a title specified
def pickKeys(d,*keys):
	from bottle import FormsDict
	if isinstance(d,dict) or not "title" in d:
		return {k:d.get(k) for k in d if k in keys}
	else:
		# create a normal dictionary of lists
		newd = {k:d.getall(k) for k in d if k in keys and k=="artist"}
		newd2 = {k:[d.get(k)] for k in d if k in keys and k!="artist"}
		# one by one add the list entries to the formsdict
		finald = FormsDict()
		for k in newd:
			for v in newd.get(k):
				finald.append(k,v)
				
		return finald
