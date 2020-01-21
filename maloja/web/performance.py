import urllib
from .. import database


def instructions(keys):
	from ..utilities import getArtistImage, getTrackImage
	from ..htmlgenerators import artistLink, artistLinks, trackLink, scrobblesLink
	from ..urihandler import compose_querystring, uri_to_internal, internal_to_uri
	from ..htmlmodules import module_performance, module_filterselection
	from ..malojatime import range_desc, delimit_desc

	filterkeys, timekeys, delimitkeys, paginatekeys = uri_to_internal(keys)

	#equivalent pulse chart
	pulselink_keys = internal_to_uri({**filterkeys,**timekeys,**delimitkeys,**paginatekeys})
	pulselink = "/pulse?" + compose_querystring(pulselink_keys)

	pulselink = "<a href=\"" + pulselink + "\"><span>View Pulse</span></a>"


	# describe the scope (and creating a key for the relevant artist or track)
	limitstring = ""
	#limitkey = {}
	if filterkeys.get("track") is not None:
		#limitkey["track"] = {"artists":keys.getall("artist"),"title":keys.get("title")}
		limitstring += "of " + trackLink(filterkeys["track"]) + " "
		limitstring += "by " + artistLinks(filterkeys["track"]["artists"])

	elif filterkeys.get("artist") is not None:
		#limitkey["artist"], limitkey["associated"] = keys.get("artist"), (keys.get("associated")!=None)
		limitstring += "of " + artistLink(filterkeys.get("artist"))
		# associated are counted by default
		data = database.artistInfo(filterkeys["artist"])
		moreartists = data["associated"]
		if moreartists != []:
			limitstring += " <span class='extra'>including " + artistLinks(moreartists) + "</span>"

	limitstring += " " + timekeys["timerange"].desc(prefix=True)

	delimitstring = delimit_desc(**delimitkeys)

	html_filterselector = module_filterselection(keys,delimit=True)


	# get image
	if filterkeys.get("track") is not None:
		imgurl = getTrackImage(filterkeys.get("track")["artists"],filterkeys.get("track")["title"])
	elif filterkeys.get("artist") is not None:
		imgurl = getArtistImage(keys.get("artist"))
	else:
		imgurl = ""

	pushresources = [{"file":imgurl,"type":"image"}] if imgurl.startswith("/") else []



	html_performance = module_performance(**filterkeys,**timekeys,**delimitkeys,**paginatekeys)

	replace = {
	"KEY_PULSE_LINK":pulselink,
	"KEY_PERFORMANCE_TABLE":html_performance,
	"KEY_IMAGEURL":imgurl,
	"KEY_LIMITS":limitstring,
	"KEY_PULSEDETAILS":delimitstring,
	"KEY_FILTERSELECTOR":html_filterselector}

	return (replace,pushresources)
