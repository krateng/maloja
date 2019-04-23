import urllib
import database


def instructions(keys):
	from utilities import getArtistImage, getTrackImage
	from htmlgenerators import artistLinks
	from urihandler import compose_querystring, uri_to_internal
	from htmlmodules import module_scrobblelist, module_pulse, module_performance


	filterkeys, _, _, _ = uri_to_internal(keys,forceTrack=True)

	track = filterkeys.get("track")
	imgurl = getTrackImage(track["artists"],track["title"],fast=True)
	pushresources = [{"file":imgurl,"type":"image"}] if imgurl.startswith("/") else []

	data = database.trackInfo(track["artists"],track["title"])

	scrobblesnum = str(data["scrobbles"])
	pos = "#" + str(data["position"])


	html_medals = ""
	if "medals" in data and data["medals"] is not None:
		if "gold" in data["medals"]:
			for y in data["medals"]["gold"]:
				html_medals += "<a  title='Best Track in " + str(y) + "' class='hidelink medal shiny gold' href='/charts_tracks?max=50&in=" + str(y) + "'><span>" + str(y) + "</span></a>"
		if "silver" in data["medals"]:
			for y in data["medals"]["silver"]:
				html_medals += "<a title='Second Best Track in " + str(y) + "' class='hidelink medal shiny silver' href='/charts_tracks?max=50&in=" + str(y) + "'><span>" + str(y) + "</span></a>"
		if "bronze" in data["medals"]:
			for y in data["medals"]["bronze"]:
				html_medals += "<a title='Third Best Track in " + str(y) + "' class='hidelink medal shiny bronze' href='/charts_tracks?max=50&in=" + str(y) + "'><span>" + str(y) + "</span></a>"



	html_scrobbles, _, _ = module_scrobblelist(track=track,max_=10,earlystop=True)	 # we have the number already from the trackinfo

	html_pulse = module_pulse(track=track,step="year",stepn=1,trail=1)
	html_performance = module_performance(track=track,step="year",stepn=1,trail=1)


	replace = {
		"KEY_TRACKTITLE":track.get("title"),
		"KEY_ARTISTS":artistLinks(track.get("artists")),
		"KEY_SCROBBLES":scrobblesnum,
		"KEY_POSITION":pos,
		"KEY_IMAGEURL":imgurl,
		"KEY_SCROBBLELINK":compose_querystring(keys),
		"KEY_MEDALS":html_medals,
		"KEY_SCROBBLELIST":html_scrobbles,
		"KEY_PULSE":html_pulse,
		"KEY_PERFORMANCE":html_performance
	}

	return (replace,pushresources)
