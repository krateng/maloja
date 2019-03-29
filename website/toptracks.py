import urllib


def instructions(keys):
	from utilities import getArtistImage, getTrackImage
	from htmlgenerators import artistLink, KeySplit
	from htmlmodules import module_trackcharts
	from malojatime import range_desc

	filterkeys, timekeys, _, amountkeys = KeySplit(keys)


	limitstring = ""


	html_charts, rep = module_trackcharts(**amountkeys,**timekeys,**filterkeys)


	if filterkeys.get("artist") is not None:
		imgurl = getArtistImage(filterkeys.get("artist"))
		limitstring = "by " + artistLink(filterkeys.get("artist"))
	elif rep is not None:
		imgurl = getTrackImage(rep["artists"],rep["title"])
	else:
		imgurl = ""

	limitstring += " " + range_desc(**timekeys)

	pushresources = [{"file":imgurl,"type":"image"}] if imgurl.startswith("/") else []



	replace = {"KEY_TOPARTIST_IMAGEURL":imgurl,"KEY_TRACKLIST":html_charts,"KEY_LIMITS":limitstring}

	return (replace,pushresources)
