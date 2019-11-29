import urllib


def instructions(keys):
	from ..utilities import getArtistImage, getTrackImage
	from ..htmlgenerators import artistLink
	from ..urihandler import compose_querystring, uri_to_internal
	from ..htmlmodules import module_trackcharts, module_filterselection, module_trackcharts_tiles
	from ..malojatime import range_desc
	from doreah.settings import get_settings

	filterkeys, timekeys, _, amountkeys = uri_to_internal(keys)

	if len(filterkeys) == 0:
		toptrackslink = "<a href='/top_tracks'><span>View #1 Tracks</span></a>"
	else:
		toptrackslink = ""


	limitstring = ""

	html_filterselector = module_filterselection(keys)

	html_charts, rep = module_trackcharts(**amountkeys,**timekeys,**filterkeys)



	html_tiles = ""

	if filterkeys.get("artist") is not None:
		imgurl = getArtistImage(filterkeys.get("artist"))
		limitstring = "by " + artistLink(filterkeys.get("artist"))
	elif rep is not None:
		imgurl = getTrackImage(rep["artists"],rep["title"])
	else:
		imgurl = ""

	html_tiles = ""
	if get_settings("CHARTS_DISPLAY_TILES"):
		html_tiles = module_trackcharts_tiles(timerange=timekeys["timerange"])
		imgurl = "favicon.png"

	imgdiv = '<div style="background-image:url('+imgurl+')"></div>'



	limitstring += " " + timekeys["timerange"].desc(prefix=True)

	pushresources = [{"file":imgurl,"type":"image"}] if imgurl.startswith("/") else []



	replace = {
		"KEY_TOPARTIST_IMAGEDIV":imgdiv,
		"KEY_TRACKCHART":html_tiles,
		"KEY_TRACKLIST":html_charts,
		"KEY_LIMITS":limitstring,
		"KEY_FILTERSELECTOR":html_filterselector,
		"TOP_TRACKS_LINK":toptrackslink,
	}

	return (replace,pushresources)
