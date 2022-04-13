import os
import math

from bottle import response, static_file, request, FormsDict

from doreah.logging import log
from doreah.auth import authenticated_api, authenticated_api_with_alternate, authenticated_function

# nimrodel API
from nimrodel import EAPI as API
from nimrodel import Multi


from .. import database
from ..globalconf import malojaconfig, data_dir



from ..__pkginfo__ import VERSION
from ..malojauri import uri_to_internal, compose_querystring, internal_to_uri
from .. import images
from ._apikeys import apikeystore, api_key_correct












api = API(delay=True)
api.__apipath__ = "mlj_1"





@api.get("test")
def test_server(key=None):
	"""Pings the server. If an API key is supplied, the server will respond with 200
	if the key is correct and 403 if it isn't. If no key is supplied, the server will
	always respond with 200.

	:param string key: An API key to be tested. Optional.
	"""
	response.set_header("Access-Control-Allow-Origin","*")
	if key is not None and not apikeystore.check_key(key):
		response.status = 403
		return {"error":"Wrong API key"}

	else:
		response.status = 200
		return {"status":"ok"}


@api.get("serverinfo")
def server_info():


	response.set_header("Access-Control-Allow-Origin","*")
	response.set_header("Content-Type","application/json")

	return {
		"name":malojaconfig["NAME"],
		"version":VERSION.split("."),
		"versionstring":VERSION,
		"db_status":database.dbstatus
	}


## API ENDPOINTS THAT CLOSELY MATCH ONE DATABASE FUNCTION


@api.get("scrobbles")
def get_scrobbles_external(**keys):
	k_filter, k_time, _, k_amount, _ = uri_to_internal(keys,api=True)
	ckeys = {**k_filter, **k_time, **k_amount}

	result = database.get_scrobbles(**ckeys)

	offset = (k_amount.get('page') * k_amount.get('perpage')) if k_amount.get('perpage') is not math.inf else 0
	result = result[offset:]
	if k_amount.get('perpage') is not math.inf: result = result[:k_amount.get('perpage')]

	return {"list":result}


# info for comparison
@api.get("info")
def info_external(**keys):

	response.set_header("Access-Control-Allow-Origin","*")
	response.set_header("Content-Type","application/json")

	return info()



@api.get("numscrobbles")
def get_scrobbles_num_external(**keys):
	k_filter, k_time, _, k_amount, _ = uri_to_internal(keys)
	ckeys = {**k_filter, **k_time, **k_amount}

	result = database.get_scrobbles_num(**ckeys)
	return {"amount":result}



@api.get("tracks")
def get_tracks_external(**keys):
	k_filter, _, _, _, _ = uri_to_internal(keys,forceArtist=True)
	ckeys = {**k_filter}

	result = database.get_tracks(**ckeys)
	return {"list":result}



@api.get("artists")
def get_artists_external():
	result = database.get_artists()
	return {"list":result}





@api.get("charts/artists")
def get_charts_artists_external(**keys):
	_, k_time, _, _, _ = uri_to_internal(keys)
	ckeys = {**k_time}

	result = database.get_charts_artists(**ckeys)
	return {"list":result}



@api.get("charts/tracks")
def get_charts_tracks_external(**keys):
	k_filter, k_time, _, _, _ = uri_to_internal(keys,forceArtist=True)
	ckeys = {**k_filter, **k_time}

	result = database.get_charts_tracks(**ckeys)
	return {"list":result}




@api.get("pulse")
def get_pulse_external(**keys):
	k_filter, k_time, k_internal, k_amount, _ = uri_to_internal(keys)
	ckeys = {**k_filter, **k_time, **k_internal, **k_amount}

	results = database.get_pulse(**ckeys)
	return {"list":results}




@api.get("performance")
def get_performance_external(**keys):
	k_filter, k_time, k_internal, k_amount, _ = uri_to_internal(keys)
	ckeys = {**k_filter, **k_time, **k_internal, **k_amount}

	results = database.get_performance(**ckeys)
	return {"list":results}




@api.get("top/artists")
def get_top_artists_external(**keys):
	_, k_time, k_internal, _, _ = uri_to_internal(keys)
	ckeys = {**k_time, **k_internal}

	results = database.get_top_artists(**ckeys)
	return {"list":results}




@api.get("top/tracks")
def get_top_tracks_external(**keys):
	_, k_time, k_internal, _, _ = uri_to_internal(keys)
	ckeys = {**k_time, **k_internal}

	# IMPLEMENT THIS FOR TOP TRACKS OF ARTIST AS WELL?

	results = database.get_top_tracks(**ckeys)
	return {"list":results}




@api.get("artistinfo")
def artist_info_external(**keys):
	k_filter, _, _, _, _ = uri_to_internal(keys,forceArtist=True)
	ckeys = {**k_filter}

	return database.artist_info(**ckeys)



@api.get("trackinfo")
def track_info_external(artist:Multi[str],**keys):
	# transform into a multidict so we can use our nomral uri_to_internal function
	keys = FormsDict(keys)
	for a in artist:
		keys.append("artist",a)
	k_filter, _, _, _, _ = uri_to_internal(keys,forceTrack=True)
	ckeys = {**k_filter}

	return database.track_info(**ckeys)


@api.get("compare")
def compare_external(**keys):
	return database.compare(keys["remote"])


@api.post("newscrobble")
@authenticated_function(alternate=api_key_correct,api=True,pass_auth_result_as='auth_result')
def post_scrobble(artist:Multi=None,auth_result=None,**keys):
	"""Submit a new scrobble.

	:param string artist: Artist. Can be submitted multiple times as query argument for multiple artists.
	:param string artists: List of artists. Overwritten by artist parameter.
	:param string title: Title of the track.
	:param string album: Name of the album. Optional.
	:param string albumartists: Album artists. Optional.
	:param int duration: Actual listened duration of the scrobble in seconds. Optional.
	:param int length: Total length of the track in seconds. Optional.
	:param int time: UNIX timestamp of the scrobble. Optional, not needed if scrobble is at time of request.
	:param boolean nofix: Skip server-side metadata parsing. Optional.
	"""

	rawscrobble = {
		'track_artists':artist if artist is not None else keys.get("artists"),
		'track_title':keys.get('title'),
		'album_name':keys.get('album'),
		'album_artists':keys.get('albumartists'),
		'scrobble_duration':keys.get('duration'),
		'track_length':keys.get('length'),
		'scrobble_time':int(keys.get('time')) if (keys.get('time') is not None) else None
	}

	# for logging purposes, don't pass values that we didn't actually supply
	rawscrobble = {k:rawscrobble[k] for k in rawscrobble if rawscrobble[k]}

	result = database.incoming_scrobble(
		rawscrobble,
		client='browser' if auth_result.get('doreah_native_auth_check') else auth_result.get('client'),
		api='native/v1',
		fix=(keys.get("nofix") is None)
	)

	if result:
		return {
			'status': 'success',
			'track': {
				'artists':result['track']['artists'],
				'title':result['track']['title']
			}
		}
	else:
		return {"status":"failure"}




@api.post("importrules")
@authenticated_api
def import_rulemodule(**keys):
	filename = keys.get("filename")
	remove = keys.get("remove") is not None
	validchars = "-_abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
	filename = "".join(c for c in filename if c in validchars)

	if remove:
		log("Deactivating predefined rulefile " + filename)
		os.remove(data_dir['rules'](filename + ".tsv"))
	else:
		log("Importing predefined rulefile " + filename)
		os.symlink(data_dir['rules']("predefined/" + filename + ".tsv"),data_dir['rules'](filename + ".tsv"))



@api.post("rebuild")
@authenticated_api
def rebuild(**keys):
	log("Database rebuild initiated!")
	database.sync()
	dbstatus['rebuildinprogress'] = True
	from ..proccontrol.tasks.fixexisting import fix
	fix()
	global cla
	cla = CleanerAgent()
	database.build_db()
	database.invalidate_caches()




@api.get("search")
def search(**keys):
	query = keys.get("query")
	max_ = keys.get("max")
	if max_ is not None: max_ = int(max_)
	query = query.lower()

	artists = database.db_search(query,type="ARTIST")
	tracks = database.db_search(query,type="TRACK")



	# if the string begins with the query it's a better match, if a word in it begins with it, still good
	# also, shorter is better (because longer titles would be easier to further specify)
	artists.sort(key=lambda x: ((0 if x.lower().startswith(query) else 1 if " " + query in x.lower() else 2),len(x)))
	tracks.sort(key=lambda x: ((0 if x["title"].lower().startswith(query) else 1 if " " + query in x["title"].lower() else 2),len(x["title"])))

	# add links
	artists_result = []
	for a in artists:
		result = {
		    'name': a,
		    'link': "/artist?" + compose_querystring(internal_to_uri({"artist": a})),
		}
		result["image"] = images.get_artist_image(a)
		artists_result.append(result)

	tracks_result = []
	for t in tracks:
		result = t
		result["link"] = "/track?" + compose_querystring(internal_to_uri({"track":t}))
		result["image"] = images.get_track_image(t)
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
	images.set_image(b64,**k_filter)


@api.post("newrule")
@authenticated_api
def newrule(**keys):
	pass
	# TODO after implementing new rule system
	#tsv.add_entry(data_dir['rules']("webmade.tsv"),[k for k in keys])
	#addEntry("rules/webmade.tsv",[k for k in keys])


@api.post("settings")
@authenticated_api
def set_settings(**keys):
	malojaconfig.update(keys)

@api.post("apikeys")
@authenticated_api
def set_apikeys(**keys):
	apikeystore.update(keys)

@api.post("import")
@authenticated_api
def import_scrobbles(identifier):
	from ..thirdparty import import_scrobbles
	import_scrobbles(identifier)

@api.get("backup")
@authenticated_api
def get_backup(**keys):
	from ..proccontrol.tasks.backup import backup
	import tempfile

	tmpfolder = tempfile.gettempdir()
	archivefile = backup(tmpfolder)

	return static_file(os.path.basename(archivefile),root=tmpfolder)

@api.get("export")
@authenticated_api
def get_export(**keys):
	from ..proccontrol.tasks.export import export
	import tempfile

	tmpfolder = tempfile.gettempdir()
	resultfile = export(tmpfolder)

	return static_file(os.path.basename(resultfile),root=tmpfolder)


@api.post("delete_scrobble")
@authenticated_api
def delete_scrobble(timestamp):
	database.remove_scrobble(timestamp)
