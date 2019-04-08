import urllib
from bottle import FormsDict
from malojatime import time_fix, time_str


# necessary because urllib.parse.urlencode doesnt handle multidicts
def compose_querystring(*dicts,exclude=[]):

	st = ""
	keys = remove_identical(*dicts)
	for k in keys:
		if k in exclude: continue
		values = keys.getall(k)
		st += "&".join([urllib.parse.urlencode({k:v},safe="/") for v in values])
		st += "&"
	return st


# takes any number of multidicts and normal dicts and creates a formsdict with duplicate values removed
def remove_identical(*dicts):
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
		#values = set(keys.getall(k))
		values = keys.getall(k)		# NO IDENTICAL REMOVAL FOR NOW
		for v in values:
			new.append(k,v)

	return new



def uri_to_internal(keys,forceTrack=False,forceArtist=False):

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
	if "since" in keys: resultkeys2["since"] = time_fix(keys.get("since"))
	elif "from" in keys: resultkeys2["since"] = time_fix(keys.get("from"))
	elif "start" in keys: resultkeys2["since"] = time_fix(keys.get("start"))
	#
	if "to" in keys: resultkeys2["to"] = time_fix(keys.get("to"))
	elif "until" in keys: resultkeys2["to"] = time_fix(keys.get("until"))
	elif "end" in keys: resultkeys2["to"] = time_fix(keys.get("end"))
	#
	if "since" in resultkeys2 and "to" in resultkeys2 and resultkeys2["since"] == resultkeys2["to"]:
		resultkeys2["within"] = resultkeys2["since"]
		del resultkeys2["since"]
		del resultkeys2["to"]
	#
	if "in" in keys: resultkeys2["within"] = time_fix(keys.get("in"))
	elif "within" in keys: resultkeys2["within"] = time_fix(keys.get("within"))
	elif "during" in keys: resultkeys2["within"] = time_fix(keys.get("during"))
	if "within" in resultkeys2:
		if "since" in resultkeys2:
			del resultkeys2["since"]
		if "to" in resultkeys2:
			del resultkeys2["to"]


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

def internal_to_uri(keys):
	urikeys = FormsDict()

	#filter
	if "artist" in keys:
		urikeys.append("artist",keys["artist"])
		if keys.get("associated"): urikeys.append("associated","yes")
	elif "track" in keys:
		for a in keys["track"]["artists"]:
			urikeys.append("artist",a)
		urikeys.append("title",keys["track"]["title"])

	#time
	if "within" in keys:
		urikeys.append("in",time_str(keys["within"]))
	else:
		if "since" in keys:
			urikeys.append("since",time_str(keys["since"]))
		if "to" in keys:
			urikeys.append("to",time_str(keys["to"]))

	# delimit
	if "step" in keys:
		urikeys.append("step",keys["step"])
	if "stepn" in keys:
		urikeys.append("stepn",str(keys["stepn"]))
	if "trail" in keys:
		urikeys.append("trail",str(keys["trail"]))

	# stuff
	if "max_" in keys:
		urikeys.append("max",str(keys["max_"]))


	return urikeys
