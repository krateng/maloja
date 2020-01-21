import urllib


def instructions(keys):
	from ..utilities import getArtistImage, getTrackImage
	from ..htmlgenerators import artistLink
	from ..urihandler import compose_querystring, uri_to_internal
	from ..htmlmodules import module_topartists, module_filterselection
	from ..malojatime import range_desc

	_, timekeys, delimitkeys, _ = uri_to_internal(keys)


	limitstring = ""

	html_filterselector = module_filterselection(keys,delimit=True)

	html_charts, rep = module_topartists(**timekeys, **delimitkeys)


	#if filterkeys.get("artist") is not None:
	#	imgurl = getArtistImage(filterkeys.get("artist"))
	#	limitstring = "by " + artistLink(filterkeys.get("artist"))
	if rep is not None:
		imgurl = getArtistImage(rep)
	else:
		imgurl = ""

	limitstring += " " + timekeys["timerange"].desc(prefix=True)

	pushresources = [{"file":imgurl,"type":"image"}] if imgurl.startswith("/") else []



	replace = {"KEY_TOPARTIST_IMAGEURL":imgurl,
	"KEY_ARTISTLIST":html_charts,
	"KEY_LIMITS":limitstring,
	"KEY_FILTERSELECTOR":html_filterselector}

	return (replace,pushresources)
