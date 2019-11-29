import urllib


def instructions(keys):
	from ..utilities import getArtistImage, getTrackImage
	from ..htmlgenerators import artistLink
	from ..urihandler import compose_querystring, uri_to_internal
	from ..htmlmodules import module_toptracks, module_filterselection
	from ..malojatime import range_desc

	filterkeys, timekeys, delimitkeys, _ = uri_to_internal(keys)


	limitstring = ""

	html_filterselector = module_filterselection(keys,delimit=True)

	html_charts, rep = module_toptracks(**timekeys, **delimitkeys) ### **filterkeys implementing?


	#if filterkeys.get("artist") is not None:
	#	imgurl = getArtistImage(filterkeys.get("artist"))
	#	limitstring = "by " + artistLink(filterkeys.get("artist"))
	if rep is not None:
		imgurl = getTrackImage(rep["artists"],rep["title"])
	else:
		imgurl = ""

	limitstring += " " + timekeys["timerange"].desc(prefix=True)

	pushresources = [{"file":imgurl,"type":"image"}] if imgurl.startswith("/") else []



	replace = {"KEY_TOPTRACK_IMAGEURL":imgurl,"KEY_TRACKLIST":html_charts,"KEY_LIMITS":limitstring,"KEY_FILTERSELECTOR":html_filterselector}

	return (replace,pushresources)
