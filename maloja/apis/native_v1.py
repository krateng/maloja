from ..database import *
from doreah import settings
from ..__pkginfo__ import version
from ..malojauri import uri_to_internal
from .. import utilities

from bottle import response

# nimrodel API
from nimrodel import EAPI as API
from nimrodel import Multi


api = API(delay=True)
api.__apipath__ = "mlj_1"


@api.get("test")
def test_server(key=None):
	response.set_header("Access-Control-Allow-Origin","*")
	if key is not None and not (checkAPIkey(key)):
		response.status = 403
		return {"error":"Wrong API key"}

	else:
		response.status = 200
		return {"status":"ok"}

	# 200	Database server is up and operational
	# 403	Database server is up, but provided API key is not valid

@api.get("serverinfo")
def server_info():


	response.set_header("Access-Control-Allow-Origin","*")
	response.set_header("Content-Type","application/json")

	return {
		"name":settings.get_settings("NAME"),
		"version":version,
		"versionstring":".".join(str(n) for n in version)
	}


## API ENDPOINTS THAT CLOSELY MATCH ONE DATABASE FUNCTION


@api.get("scrobbles")
def get_scrobbles_external(**keys):
	k_filter, k_time, _, k_amount = uri_to_internal(keys)
	ckeys = {**k_filter, **k_time, **k_amount}

	result = get_scrobbles(**ckeys)
	return {"list":result}


# info for comparison
@api.get("info")
def info_external(**keys):

	response.set_header("Access-Control-Allow-Origin","*")
	response.set_header("Content-Type","application/json")

	result = info()
	return result



@api.get("numscrobbles")
def get_scrobbles_num_external(**keys):
	k_filter, k_time, _, k_amount = uri_to_internal(keys)
	ckeys = {**k_filter, **k_time, **k_amount}

	result = get_scrobbles_num(**ckeys)
	return {"amount":result}



@api.get("tracks")
def get_tracks_external(**keys):
	k_filter, _, _, _ = uri_to_internal(keys,forceArtist=True)
	ckeys = {**k_filter}

	result = get_tracks(**ckeys)
	return {"list":result}



@api.get("artists")
def get_artists_external():
	result = get_artists()
	return {"list":result}





@api.get("charts/artists")
def get_charts_artists_external(**keys):
	_, k_time, _, _ = uri_to_internal(keys)
	ckeys = {**k_time}

	result = get_charts_artists(**ckeys)
	return {"list":result}



@api.get("charts/tracks")
def get_charts_tracks_external(**keys):
	k_filter, k_time, _, _ = uri_to_internal(keys,forceArtist=True)
	ckeys = {**k_filter, **k_time}

	result = get_charts_tracks(**ckeys)
	return {"list":result}




@api.get("pulse")
def get_pulse_external(**keys):
	k_filter, k_time, k_internal, k_amount = uri_to_internal(keys)
	ckeys = {**k_filter, **k_time, **k_internal, **k_amount}

	results = get_pulse(**ckeys)
	return {"list":results}




@api.get("performance")
def get_performance_external(**keys):
	k_filter, k_time, k_internal, k_amount = uri_to_internal(keys)
	ckeys = {**k_filter, **k_time, **k_internal, **k_amount}

	results = get_performance(**ckeys)
	return {"list":results}




@api.get("top/artists")
def get_top_artists_external(**keys):
	_, k_time, k_internal, _ = uri_to_internal(keys)
	ckeys = {**k_time, **k_internal}

	results = get_top_artists(**ckeys)
	return {"list":results}




@api.get("top/tracks")
def get_top_tracks_external(**keys):
	_, k_time, k_internal, _ = uri_to_internal(keys)
	ckeys = {**k_time, **k_internal}

	# IMPLEMENT THIS FOR TOP TRACKS OF ARTIST AS WELL?

	results = get_top_tracks(**ckeys)
	return {"list":results}




@api.get("artistinfo")
def artistInfo_external(**keys):
	k_filter, _, _, _ = uri_to_internal(keys,forceArtist=True)
	ckeys = {**k_filter}

	results = artistInfo(**ckeys)
	return results



@api.get("trackinfo")
def trackInfo_external(artist:Multi[str],**keys):
	# transform into a multidict so we can use our nomral uri_to_internal function
	keys = FormsDict(keys)
	for a in artist:
		keys.append("artist",a)
	k_filter, _, _, _ = uri_to_internal(keys,forceTrack=True)
	ckeys = {**k_filter}

	results = trackInfo(**ckeys)
	return results


@api.get("compare")
def compare_external(**keys):

	results = compare(keys["remote"])
	return results



@api.get("newscrobble")
@api.post("newscrobble")
@authenticated_api_with_alternate(api_key_correct)
def post_scrobble(artist:Multi,**keys):
	#artists = "/".join(artist)
	artists = artist
	title = keys.get("title")
	album = keys.get("album")
	duration = keys.get("seconds")
	time = keys.get("time")
	if time is not None: time = int(time)

	return incoming_scrobble(artists,title,album=album,duration=duration,time=time)




@api.post("importrules")
@authenticated_api
def import_rulemodule(**keys):
	filename = keys.get("filename")
	remove = keys.get("remove") is not None
	validchars = "-_abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
	filename = "".join(c for c in filename if c in validchars)

	if remove:
		log("Deactivating predefined rulefile " + filename)
		os.remove(datadir("rules/" + filename + ".tsv"))
	else:
		log("Importing predefined rulefile " + filename)
		os.symlink(datadir("rules/predefined/" + filename + ".tsv"),datadir("rules/" + filename + ".tsv"))



@api.post("rebuild")
@authenticated_api
def rebuild(**keys):
	log("Database rebuild initiated!")
	sync()
	from .proccontrol.tasks.fixexisting import fix
	fix()
	global cla, coa
	cla = CleanerAgent()
	coa = CollectorAgent()
	build_db()
	invalidate_caches()




@api.get("search")
def search(**keys):
	query = keys.get("query")
	max_ = keys.get("max")
	if max_ is not None: max_ = int(max_)
	query = query.lower()

	artists = db_search(query,type="ARTIST")
	tracks = db_search(query,type="TRACK")



	# if the string begins with the query it's a better match, if a word in it begins with it, still good
	# also, shorter is better (because longer titles would be easier to further specify)
	artists.sort(key=lambda x: ((0 if x.lower().startswith(query) else 1 if " " + query in x.lower() else 2),len(x)))
	tracks.sort(key=lambda x: ((0 if x["title"].lower().startswith(query) else 1 if " " + query in x["title"].lower() else 2),len(x["title"])))

	# add links
	artists_result = []
	for a in artists:
		result = {"name":a}
		result["link"] = "/artist?" + compose_querystring(internal_to_uri({"artist":a}))
		result["image"] = "/image?" + compose_querystring(internal_to_uri({"artist":a}))
		artists_result.append(result)

	tracks_result = []
	for t in tracks:
		result = t
		result["link"] = "/track?" + compose_querystring(internal_to_uri({"track":t}))
		result["image"] = "/image?" + compose_querystring(internal_to_uri({"track":t}))
		tracks_result.append(result)

	return {"artists":artists_result[:max_],"tracks":tracks_result[:max_]}


@api.post("addpicture")
@authenticated_api
def add_picture(b64,artist:Multi=[],title=None):
	keys = FormsDict()
	for a in artist:
		keys.append("artist",a)
	if title is not None: keys.append("title",title)
	k_filter, _, _, _, _ = uri_to_internal(keys)
	if "track" in k_filter: k_filter = k_filter["track"]
	utilities.set_image(b64,**k_filter)


@api.post("newrule")
@authenticated_api
def newrule(**keys):
	tsv.add_entry(datadir("rules/webmade.tsv"),[k for k in keys])
	#addEntry("rules/webmade.tsv",[k for k in keys])
