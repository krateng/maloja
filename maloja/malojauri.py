from .malojatime import get_range_object



# this also sets defaults!
def uri_to_internal(keys,forceTrack=False,forceArtist=False):

	# output:
	# 1	keys that define the filtered object like artist or track
	# 2	keys that define time limits of the whole thing
	# 3	keys that define interal time ranges
	# 4	keys that define amount limits

	# 1
	if "title" in keys and not forceArtist:
		filterkeys = {"track":{"artists":keys.getall("artist"),"title":keys.get("title")}}
	elif "artist" in keys and not forceTrack:
		filterkeys = {"artist":keys.get("artist")}
		if "associated" in keys: resultkeys1["associated"] = True
	else:
		filterkeys = {}

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
	delimitkeys = {"step":"month","stepn":1,"trail":1}
	if "step" in keys: [delimitkeys["step"],delimitkeys["stepn"]] = (keys["step"].split("-") + [1])[:2]
	if "stepn" in keys: delimitkeys["stepn"] = keys["stepn"] #overwrite if explicitly given
	if "stepn" in delimitkeys: delimitkeys["stepn"] = int(delimitkeys["stepn"]) #in both cases, convert it here
	if "trail" in keys: delimitkeys["trail"] = int(keys["trail"])
	if "cumulative" in keys: delimitkeys["trail"] = math.inf



	#4
	amountkeys = {"page":0,"perpage":100}
	if "max" in keys: amountkeys["page"],amountkeys["perpage"] = 0, int(keys["max"])
	#different max than the internal one! the user doesn't get to disable pagination
	if "page" in keys: amountkeys["page"] = int(keys["page"])
	if "perpage" in keys: amountkeys["perpage"] = int(keys["perpage"])


	#5
	specialkeys = {}
	if "remote" in keys: specialkeys["remote"] = keys["remote"]


	return filterkeys, limitkeys, delimitkeys, amountkeys, specialkeys
