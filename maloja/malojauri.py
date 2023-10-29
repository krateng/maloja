from .malojatime import get_range_object
from bottle import FormsDict
import urllib
import math

# this also sets defaults!
def uri_to_internal(keys,accepted_entities=('artist','track','album'),forceTrack=False,forceArtist=False,forceAlbum=False,api=False):

	# output:
	# 1	keys that define the filtered object like artist or track
	# 2	keys that define time limits of the whole thing
	# 3	keys that define interal time ranges
	# 4	keys that define amount limits

	# if we force a type, that only means that the other types are not allowed
	# it could still have no type at all (any call that isn't filtering by entity)

	if forceTrack: accepted_entities = ('track',)
	if forceArtist: accepted_entities = ('artist',)
	if forceAlbum: accepted_entities = ('album',)

	# API backwards compatibility
	if "artist" in keys and "artist" not in accepted_entities:
		if "track" in accepted_entities:
			keys['trackartist'] = keys['artist']
		elif "album" in accepted_entities:
			keys['albumartist'] = keys['artist']


	# 1
	filterkeys = {}
	if "track" in accepted_entities and "title" in keys:
		filterkeys.update({"track":{"artists":keys.getall("trackartist"),"title":keys.get("title")}})
	if "artist" in accepted_entities and "artist" in keys:
		filterkeys.update({"artist": keys.get("artist"), "associated": (keys.get('associated', 'no').lower() == 'yes')})
		# associated is only used for filtering by artist, to indicate that we include associated artists
		# for actual artist charts, to show that we want to count them, use 'unified'
	if "album" in accepted_entities and "albumtitle" in keys:
		filterkeys.update({"album":{"artists":keys.getall("albumartist"),"albumtitle":keys.get("albumtitle")}})



	# 2
	limitkeys = {}
	since,to,within = None,None,None
	if "since" in keys: since = keys.get("since")
	elif "from" in keys: since = keys.get("from")
	elif "start" in keys: since = keys.get("start")
	if "to" in keys: to = keys.get("to")
	elif "until" in keys: to = keys.get("until")
	elif "end" in keys: to = keys.get("end")
	if "in" in keys: within = keys.get("in")
	elif "within" in keys: within = keys.get("within")
	elif "during" in keys: within = keys.get("during")
	limitkeys["timerange"] = get_range_object(since=since,to=to,within=within)

	#3
	delimitkeys = {"step":"year","stepn":1,"trail":1}
	if "step" in keys: [delimitkeys["step"],delimitkeys["stepn"]] = (keys["step"].split("-") + [1])[:2]
	if "stepn" in keys: delimitkeys["stepn"] = keys["stepn"] #overwrite if explicitly given
	if "stepn" in delimitkeys: delimitkeys["stepn"] = int(delimitkeys["stepn"]) #in both cases, convert it here
	if "trail" in keys: delimitkeys["trail"] = int(keys["trail"])
	if "cumulative" in keys: delimitkeys["trail"] = math.inf



	#4
	amountkeys = {"page":0,"perpage":math.inf if api else 100} # api doesnt paginate per default
	if "max" in keys: amountkeys["page"],amountkeys["perpage"] = 0, int(keys["max"])
	#different max than the internal one! the user doesn't get to disable pagination
	if "page" in keys: amountkeys["page"] = int(keys["page"])
	if "perpage" in keys: amountkeys["perpage"] = int(keys["perpage"])
	#amountkeys["reverse"] = (keys.get("reverse","no").lower() == "yes")
	# we have different defaults for different things, so here we need to actually pass true false or nothing dependent
	# on whether its specified
	if keys.get("reverse","").lower() == 'yes': amountkeys['reverse'] = True
	elif keys.get("reverse","").lower() == 'no': amountkeys['reverse'] = False

	#5
	specialkeys = {}
	#if "remote" in keys: specialkeys["remote"] = keys["remote"]
	specialkeys["separate"] = (keys.get('separate','no').lower() == 'yes')
	for k in keys:
		if k in ['remote','b64']:
			# TODO: better solution!
			specialkeys[k] = keys[k]


	return filterkeys, limitkeys, delimitkeys, amountkeys, specialkeys



def create_uri(path,*keydicts):
	return path + "?" + uriencode(*keydicts)

def uriencode(*keydicts):
	keyd = {}
	for kd in keydicts:
		keyd.update(kd)

	return compose_querystring(internal_to_uri(keyd))


def internal_to_uri(keys):
	urikeys = FormsDict()

	#filter
	if "artist" in keys:
		urikeys.append("artist",keys["artist"])
		if keys.get("associated"): urikeys.append("associated","yes")
	if "track" in keys:
		for a in keys["track"]["artists"]:
			urikeys.append("trackartist",a)
		urikeys.append("title",keys["track"]["title"])
	if "album" in keys:
		for a in keys["album"].get("artists") or []:
			urikeys.append("albumartist",a)
		urikeys.append("albumtitle",keys["album"]["albumtitle"])


	#time
	if "timerange" in keys:
		keydict = keys["timerange"].urikeys()
		for k in keydict:
			urikeys.append(k,keydict[k])
	elif "within" in keys:
		urikeys.append("in",time_str(keys["within"]))
	else:
		if "since" in keys and keys["since"] is not None:
			urikeys.append("since",time_str(keys["since"]))
		if "to" in keys and keys["to"] is not None:
			urikeys.append("to",time_str(keys["to"]))

	# delimit
	if "step" in keys:
		urikeys.append("step",keys["step"])
	if "stepn" in keys:
		urikeys.append("stepn",str(keys["stepn"]))
	if "trail" in keys:
		if keys["trail"] == math.inf:
			urikeys.append("cumulative","yes")
		else:
			urikeys.append("trail",str(keys["trail"]))

	# stuff
	#if "max_" in keys:
	#	urikeys.append("max",str(keys["max_"]))
	if "page" in keys:
		urikeys.append("page",str(keys["page"]))
	if "perpage" in keys:
		urikeys.append("perpage",str(keys["perpage"]))
	if "reverse" in keys:
		urikeys.append("reverse","yes" if keys['reverse'] else "no")

	if keys.get("separate",False):
		urikeys.append("separate","yes")


	return urikeys





# necessary because urllib.parse.urlencode doesnt handle multidicts
def compose_querystring(*dicts,exclude=[]):

	st = ""
	keys = remove_identical(*dicts)
	for k in keys:
		if k in exclude: continue
		values = keys.getall(k)
		st += "&".join(urllib.parse.urlencode({k:v},safe="/") for v in values)
		st += "&"
	return st[:-1] if st.endswith("&") else st  # remove last ampersand


# takes any number of multidicts and normal dicts and creates a formsdict with duplicate values removed
def remove_identical(*dicts):
	#combine multiple dicts
	keys = FormsDict()
	for d in dicts:
		for k in d:
			try: #multidicts
				for v in d.getall(k):
					keys.append(k,v)
			except Exception: #normaldicts
				v = d.get(k)
				keys.append(k,v)

	return keys
