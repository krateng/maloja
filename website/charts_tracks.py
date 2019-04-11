import urllib


def instructions(keys):
	from utilities import getArtistImage, getTrackImage
	from htmlgenerators import artistLink
	from urihandler import compose_querystring, uri_to_internal
	from htmlmodules import module_trackcharts, module_filterselection
	from malojatime import range_desc

	filterkeys, timekeys, _, amountkeys = uri_to_internal(keys)


	limitstring = ""

	html_filterselector = module_filterselection(keys)

	html_charts, rep = module_trackcharts(**amountkeys,**timekeys,**filterkeys)


	if filterkeys.get("artist") is not None:
		imgurl = getArtistImage(filterkeys.get("artist"))
		limitstring = "by " + artistLink(filterkeys.get("artist"))
	elif rep is not None:
		imgurl = getTrackImage(rep["artists"],rep["title"])
	else:
		imgurl = ""

	limitstring += " " + timekeys["timerange"].desc(prefix=True)

	pushresources = [{"file":imgurl,"type":"image"}] if imgurl.startswith("/") else []



	replace = {"KEY_TOPARTIST_IMAGEURL":imgurl,"KEY_TRACKLIST":html_charts,"KEY_LIMITS":limitstring,"KEY_FILTERSELECTOR":html_filterselector}

	return (replace,pushresources)
