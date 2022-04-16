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




errors = {
	database.MissingScrobbleParameters: lambda e: (400,{
		"status":"failure",
		"error":{
			'type':'missing_scrobble_data',
			'value':e.params,
			'desc':"A scrobble requires these parameters."
		}
	}),
	Exception: lambda e: (500,{
		"status":"failure",
		"error":{
			'type':'unknown_error',
			'value':e.__repr__(),
			'desc':"The server has encountered an exception."
		}
	})
}



def add_common_args_to_docstring(filterkeys=False,limitkeys=False,delimitkeys=False,amountkeys=False):
	def decorator(func):
		timeformats = "Possible formats include '2022', '2022/08', '2022/08/01', '2022/W42', 'today', 'thismonth', 'monday', 'august'"

		if filterkeys:
			func.__doc__ += f"""
				:param string title: Track title
				:param string artist: Track artist. Can be specified multiple times.
				:param bool associated: Whether to include associated artists.
				"""
		if limitkeys:
			func.__doc__ += f"""
				:param string from: Start of the desired time range. Can also be called since or start. {timeformats}
				:param string until: End of the desired range. Can also be called to or end. {timeformats}
				:param string in: Desired range. Can also be called within or during. {timeformats}
			"""
		if delimitkeys:
			func.__doc__ += """
				:param string step: Step, e.g. month or week.
				:param int stepn: Number of base type units per step
				:param int trail: How many preceding steps should be factored in.
				:param bool cumulative: Instead of a fixed trail length, use all history up to this point.
			"""
		if amountkeys:
			func.__doc__ += """
				:param int page: Page to show
				:param int perpage: Entries per page.
				:param int max: Legacy. Show first page with this many entries.
			"""
		return func
	return decorator



@api.get("test")
def test_server(key=None):
	"""Pings the server. If an API key is supplied, the server will respond with 200
	if the key is correct and 403 if it isn't. If no key is supplied, the server will
	always respond with 200.

	:param string key: An API key to be tested. Optional.
	:return: status (String), error (String)
	:rtype: Dictionary
	"""
	response.set_header("Access-Control-Allow-Origin","*")
	if key is not None and not apikeystore.check_key(key):
		response.status = 403
		return {
			"status":"error",
			"error":"Wrong API key"
		}

	else:
		response.status = 200
		return {
			"status":"ok"
		}


@api.get("serverinfo")
def server_info():
	"""Returns basic information about the server.

	:return: name (String), version (Tuple), versionstring (String), db_status (Mapping). Additional keys can be added at any point, but will not be removed within API version.
	:rtype: Dictionary
	"""


	response.set_header("Access-Control-Allow-Origin","*")

	return {
		"name":malojaconfig["NAME"],
		"version":VERSION.split("."),
		"versionstring":VERSION,
		"db_status":database.dbstatus
	}


## API ENDPOINTS THAT CLOSELY MATCH ONE DATABASE FUNCTION


@api.get("scrobbles")
@add_common_args_to_docstring(filterkeys=True,limitkeys=True,amountkeys=True)
def get_scrobbles_external(**keys):
	"""Returns a list of scrobbles.

	:return: list (List)
	:rtype: Dictionary
	"""
	k_filter, k_time, _, k_amount, _ = uri_to_internal(keys,api=True)
	ckeys = {**k_filter, **k_time, **k_amount}

	result = database.get_scrobbles(**ckeys)

	offset = (k_amount.get('page') * k_amount.get('perpage')) if k_amount.get('perpage') is not math.inf else 0
	result = result[offset:]
	if k_amount.get('perpage') is not math.inf: result = result[:k_amount.get('perpage')]

	return {
		"list":result
	}


@api.get("numscrobbles")
@add_common_args_to_docstring(filterkeys=True,limitkeys=True,amountkeys=True)
def get_scrobbles_num_external(**keys):
	"""Returns amount of scrobbles.

	:return: amount (Integer)
	:rtype: Dictionary
	"""
	k_filter, k_time, _, k_amount, _ = uri_to_internal(keys)
	ckeys = {**k_filter, **k_time, **k_amount}

	result = database.get_scrobbles_num(**ckeys)

	return {
		"amount":result
	}



@api.get("tracks")
@add_common_args_to_docstring(filterkeys=True)
def get_tracks_external(**keys):
	"""Returns all tracks (optionally of an artist).

	:return: list (List)
	:rtype: Dictionary
	"""
	k_filter, _, _, _, _ = uri_to_internal(keys,forceArtist=True)
	ckeys = {**k_filter}

	result = database.get_tracks(**ckeys)

	return {
		"list":result
	}



@api.get("artists")
@add_common_args_to_docstring()
def get_artists_external():
	"""Returns all artists.

	:return: list (List)
	:rtype: Dictionary"""
	result = database.get_artists()

	return {
		"list":result
	}





@api.get("charts/artists")
@add_common_args_to_docstring(limitkeys=True)
def get_charts_artists_external(**keys):
	"""Returns artist charts

	:return: list (List)
	:rtype: Dictionary"""
	_, k_time, _, _, _ = uri_to_internal(keys)
	ckeys = {**k_time}

	result = database.get_charts_artists(**ckeys)

	return {
		"list":result
	}



@api.get("charts/tracks")
@add_common_args_to_docstring(filterkeys=True,limitkeys=True)
def get_charts_tracks_external(**keys):
	"""Returns track charts

	:return: list (List)
	:rtype: Dictionary"""
	k_filter, k_time, _, _, _ = uri_to_internal(keys,forceArtist=True)
	ckeys = {**k_filter, **k_time}

	result = database.get_charts_tracks(**ckeys)

	return {
		"list":result
	}




@api.get("pulse")
@add_common_args_to_docstring(filterkeys=True,limitkeys=True,delimitkeys=True,amountkeys=True)
def get_pulse_external(**keys):
	"""Returns amounts of scrobbles in specified time frames

	:return: list (List)
	:rtype: Dictionary"""
	k_filter, k_time, k_internal, k_amount, _ = uri_to_internal(keys)
	ckeys = {**k_filter, **k_time, **k_internal, **k_amount}

	results = database.get_pulse(**ckeys)

	return {
		"list":results
	}




@api.get("performance")
@add_common_args_to_docstring(filterkeys=True,limitkeys=True,delimitkeys=True,amountkeys=True)
def get_performance_external(**keys):
	"""Returns artist's or track's rank in specified time frames

	:return: list (List)
	:rtype: Dictionary"""
	k_filter, k_time, k_internal, k_amount, _ = uri_to_internal(keys)
	ckeys = {**k_filter, **k_time, **k_internal, **k_amount}

	results = database.get_performance(**ckeys)

	return {
		"list":results
	}




@api.get("top/artists")
@add_common_args_to_docstring(limitkeys=True,delimitkeys=True)
def get_top_artists_external(**keys):
	"""Returns respective number 1 artists in specified time frames

	:return: list (List)
	:rtype: Dictionary"""
	_, k_time, k_internal, _, _ = uri_to_internal(keys)
	ckeys = {**k_time, **k_internal}

	results = database.get_top_artists(**ckeys)

	return {
		"list":results
	}




@api.get("top/tracks")
@add_common_args_to_docstring(limitkeys=True,delimitkeys=True)
def get_top_tracks_external(**keys):
	"""Returns respective number 1 tracks in specified time frames

	:return: list (List)
	:rtype: Dictionary"""
	_, k_time, k_internal, _, _ = uri_to_internal(keys)
	ckeys = {**k_time, **k_internal}

	# IMPLEMENT THIS FOR TOP TRACKS OF ARTIST AS WELL?

	results = database.get_top_tracks(**ckeys)

	return {
		"list":results
	}




@api.get("artistinfo")
@add_common_args_to_docstring(filterkeys=True)
def artist_info_external(**keys):
	"""Returns information about an artist

	:return: artist (String), scrobbles (Integer), position (Integer), associated (List), medals (Mapping), topweeks (Integer)
	:rtype: Dictionary"""
	k_filter, _, _, _, _ = uri_to_internal(keys,forceArtist=True)
	ckeys = {**k_filter}

	return database.artist_info(**ckeys)



@api.get("trackinfo")
@add_common_args_to_docstring(filterkeys=True)
def track_info_external(artist:Multi[str],**keys):
	"""Returns information about a track

	:return: track (Mapping), scrobbles (Integer), position (Integer), medals (Mapping), certification (String), topweeks (Integer)
	:rtype: Dictionary"""
	# transform into a multidict so we can use our nomral uri_to_internal function
	keys = FormsDict(keys)
	for a in artist:
		keys.append("artist",a)
	k_filter, _, _, _, _ = uri_to_internal(keys,forceTrack=True)
	ckeys = {**k_filter}

	return database.track_info(**ckeys)


@api.post("newscrobble")
@authenticated_function(alternate=api_key_correct,api=True,pass_auth_result_as='auth_result')
def post_scrobble(
		artist:Multi=None,
		artists:list=[],
		title:str="",
		album:str=None,
		albumartists:list=[],
		duration:int=None,
		length:int=None,
		time:int=None,
		nofix=None,
		auth_result=None,
		**extra_kwargs):
	"""Submit a new scrobble.

	:param string artist: Artist. Can be submitted multiple times as query argument for multiple artists.
	:param list artists: List of artists.
	:param string title: Title of the track.
	:param string album: Name of the album. Optional.
	:param list albumartists: Album artists. Optional.
	:param int duration: Actual listened duration of the scrobble in seconds. Optional.
	:param int length: Total length of the track in seconds. Optional.
	:param int time: UNIX timestamp of the scrobble. Optional, not needed if scrobble is at time of request.
	:param flag nofix: Skip server-side metadata parsing. Optional.

	:return: status (String), track (Mapping)
	:rtype: Dictionary
	"""

	rawscrobble = {
		'track_artists':(artist or []) + artists,
		'track_title':title,
		'album_name':album,
		'album_artists':albumartists,
		'scrobble_duration':duration,
		'track_length':length,
		'scrobble_time':time
	}

	# for logging purposes, don't pass values that we didn't actually supply
	rawscrobble = {k:rawscrobble[k] for k in rawscrobble if rawscrobble[k]}

	try:
		result = database.incoming_scrobble(
			rawscrobble,
			client='browser' if auth_result.get('doreah_native_auth_check') else auth_result.get('client'),
			api='native/v1',
			fix=(nofix is None)
		)

		responsedict = {
			'status': 'success',
			'track': {
				'artists':result['track']['artists'],
				'title':result['track']['title']
			}
		}
		if extra_kwargs:
			responsedict['warnings'] = [
				{'type':'invalid_keyword_ignored','value':k,
				'desc':"This key was not recognized by the server and has been discarded."}
				for k in extra_kwargs
			]
		if artist and artists:
			responsedict['warnings'] = [
				{'type':'mixed_schema','value':['artist','artists'],
				'desc':"These two fields are meant as alternative methods to submit information. Use of both is discouraged, but works at the moment."}
			]
		return responsedict
	except Exception as e:
		for etype in errors:
			if isinstance(e,etype):
				errorhandling = errors[etype](e)
				response.status = errorhandling[0]
				return errorhandling[1]





@api.post("importrules")
@authenticated_function(api=True)
def import_rulemodule(**keys):
	"""Internal Use Only"""
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
@authenticated_function(api=True)
def rebuild(**keys):
	"""Internal Use Only"""
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
	"""Internal Use Only"""
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
@authenticated_function(api=True)
def add_picture(b64,artist:Multi=[],title=None):
	"""Internal Use Only"""
	keys = FormsDict()
	for a in artist:
		keys.append("artist",a)
	if title is not None: keys.append("title",title)
	k_filter, _, _, _, _ = uri_to_internal(keys)
	if "track" in k_filter: k_filter = k_filter["track"]
	images.set_image(b64,**k_filter)


@api.post("newrule")
@authenticated_function(api=True)
def newrule(**keys):
	"""Internal Use Only"""
	pass
	# TODO after implementing new rule system
	#tsv.add_entry(data_dir['rules']("webmade.tsv"),[k for k in keys])
	#addEntry("rules/webmade.tsv",[k for k in keys])


@api.post("settings")
@authenticated_function(api=True)
def set_settings(**keys):
	"""Internal Use Only"""
	malojaconfig.update(keys)

@api.post("apikeys")
@authenticated_function(api=True)
def set_apikeys(**keys):
	"""Internal Use Only"""
	apikeystore.update(keys)

@api.post("import")
@authenticated_function(api=True)
def import_scrobbles(identifier):
	"""Internal Use Only"""
	from ..thirdparty import import_scrobbles
	import_scrobbles(identifier)

@api.get("backup")
@authenticated_function(api=True)
def get_backup(**keys):
	"""Internal Use Only"""
	from ..proccontrol.tasks.backup import backup
	import tempfile

	tmpfolder = tempfile.gettempdir()
	archivefile = backup(tmpfolder)

	return static_file(os.path.basename(archivefile),root=tmpfolder)

@api.get("export")
@authenticated_function(api=True)
def get_export(**keys):
	"""Internal Use Only"""
	from ..proccontrol.tasks.export import export
	import tempfile

	tmpfolder = tempfile.gettempdir()
	resultfile = export(tmpfolder)

	return static_file(os.path.basename(resultfile),root=tmpfolder)


@api.post("delete_scrobble")
@authenticated_function(api=True)
def delete_scrobble(timestamp):
	"""Internal Use Only"""
	database.remove_scrobble(timestamp)
