import urllib
import database


def instructions(keys):
	from utilities import getArtistImage
	from htmlgenerators import artistLink, artistLinks
	from urihandler import compose_querystring, uri_to_internal
	from htmlmodules import module_pulse, module_trackcharts

	filterkeys, _, _, _ = uri_to_internal(keys,forceArtist=True)
	imgurl = getArtistImage(filterkeys["artist"],fast=True)
	pushresources = [{"file":imgurl,"type":"image"}] if imgurl.startswith("/") else []

	data = database.artistInfo(filterkeys["artist"])
	scrobbles = str(data["scrobbles"])
	pos = "#" + str(data["position"])

	html_medals = ""
	if "medals" in data and data["medals"] is not None:
		if "gold" in data["medals"]:
			for y in data["medals"]["gold"]:
				html_medals += "<a  title='Best Artist in " + str(y) + "' class='hidelink medal shiny gold' href='/charts_artists?max=50&in=" + str(y) + "'><span>" + str(y) + "</span></a>"
		if "silver" in data["medals"]:
			for y in data["medals"]["silver"]:
				html_medals += "<a title='Second Best Artist in " + str(y) + "' class='hidelink medal shiny silver' href='/charts_artists?max=50&in=" + str(y) + "'><span>" + str(y) + "</span></a>"
		if "bronze" in data["medals"]:
			for y in data["medals"]["bronze"]:
				html_medals += "<a title='Third Best Artist in " + str(y) + "' class='hidelink medal shiny bronze' href='/charts_artists?max=50&in=" + str(y) + "'><span>" + str(y) + "</span></a>"

	credited = data.get("replace")
	includestr = " "
	if credited is not None:
		includestr = "Competing under " + artistLink(credited) + " (" + pos + ")"
		pos = ""
	included = data.get("associated")
	if included is not None and included != []:
		includestr = "associated: "
		includestr += artistLinks(included)


	html_tracks, _ = module_trackcharts(**filterkeys,max_=15)


	html_pulse = module_pulse(**filterkeys,step="year",stepn=1,trail=1)

	replace = {"KEY_ARTISTNAME":keys["artist"],"KEY_ENC_ARTISTNAME":urllib.parse.quote(keys["artist"]),
	"KEY_IMAGEURL":imgurl, "KEY_DESCRIPTION":"","KEY_MEDALS":html_medals,
	"KEY_TRACKLIST":html_tracks,"KEY_PULSE":html_pulse,
	"KEY_SCROBBLES":scrobbles,"KEY_POSITION":pos,
	"KEY_ASSOCIATED":includestr}

	return (replace,pushresources)
