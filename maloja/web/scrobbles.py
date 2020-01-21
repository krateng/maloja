import urllib
from .. import database


def instructions(keys):
	from ..utilities import getArtistImage, getTrackImage
	from ..htmlgenerators import artistLink, artistLinks, trackLink
	from ..urihandler import compose_querystring, uri_to_internal
	from ..htmlmodules import module_scrobblelist, module_filterselection
	from ..malojatime import range_desc


	filterkeys, timekeys, _, amountkeys = uri_to_internal(keys)

	# describe the scope
	limitstring = ""
	if filterkeys.get("track") is not None:
		limitstring += "of " + trackLink(filterkeys["track"]) + " "
		limitstring += "by " + artistLinks(filterkeys["track"]["artists"])

	elif filterkeys.get("artist") is not None:
		limitstring += "by " + artistLink(filterkeys.get("artist"))
		if filterkeys.get("associated"):
			data = database.artistInfo(filterkeys["artist"])
			moreartists = data.get("associated")
			if moreartists != []:
				limitstring += " <span class='extra'>including " + artistLinks(moreartists) + "</span>"

	limitstring += " " + timekeys["timerange"].desc(prefix=True)

	html_filterselector = module_filterselection(keys)


	html, amount, rep = module_scrobblelist(**filterkeys,**timekeys,**amountkeys)

	# get image
	if filterkeys.get("track") is not None:
		imgurl = getTrackImage(filterkeys.get("track")["artists"],filterkeys.get("track")["title"],fast=True)
	elif filterkeys.get("artist") is not None:
		imgurl = getArtistImage(keys.get("artist"),fast=True)
	elif rep is not None:
		imgurl = getTrackImage(rep["artists"],rep["title"],fast=True)
	else:
		imgurl = ""


	pushresources = [{"file":imgurl,"type":"image"}] if imgurl.startswith("/") else []


	replace = {"KEY_SCROBBLELIST":html,
	"KEY_SCROBBLES":str(amount),
	"KEY_IMAGEURL":imgurl,
	"KEY_LIMITS":limitstring,
	"KEY_FILTERSELECTOR":html_filterselector}

	return (replace,pushresources)
