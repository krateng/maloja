import urllib
import database
from malojatime import today,thisweek,thismonth,thisyear


def instructions(keys):
	from utilities import getArtistImage
	from htmlgenerators import artistLink, artistLinks
	from urihandler import compose_querystring, uri_to_internal
	from htmlmodules import module_pulse, module_performance, module_trackcharts, module_scrobblelist

	filterkeys, _, _, _ = uri_to_internal(keys,forceArtist=True)
	artist = filterkeys.get("artist")
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
	else:
		credited = artist
	included = data.get("associated")
	if included is not None and included != []:
		includestr = "associated: "
		includestr += artistLinks(included)


	html_tracks, _ = module_trackcharts(**filterkeys,max_=15)

	html_scrobbles, _, _ = module_scrobblelist(artist=artist,max_=10,earlystop=True)

	# pulse and rankings
	html_pulse_days = module_pulse(**filterkeys,max_=7,since=today().next(-6),step="day",trail=1)
	html_pulse_weeks = module_pulse(**filterkeys,max_=12,since=thisweek().next(-11),step="week",trail=1)
	html_pulse_months = module_pulse(**filterkeys,max_=12,since=thismonth().next(-11),step="month",trail=1)
	html_pulse_years = module_pulse(**filterkeys,max_=10,since=thisyear().next(-9),step="year",trail=1)

	html_performance_days = module_performance(artist=credited,max_=7,since=today().next(-6),step="day",trail=1)
	html_performance_weeks = module_performance(artist=credited,max_=12,since=thisweek().next(-11),step="week",trail=1)
	html_performance_months = module_performance(artist=credited,max_=12,since=thismonth().next(-11),step="month",trail=1)
	html_performance_years = module_performance(artist=credited,max_=10,since=thisyear().next(-9),step="year",trail=1)

	replace = {
		# info
		"KEY_ARTISTNAME":keys["artist"],
		"KEY_ENC_ARTISTNAME":urllib.parse.quote(keys["artist"]),
		"KEY_ENC_CREDITEDARTISTNAME":urllib.parse.quote(credited),
		"KEY_IMAGEURL":imgurl,
		"KEY_DESCRIPTION":"",
		"KEY_SCROBBLES":scrobbles,
		"KEY_POSITION":pos,
		"KEY_ASSOCIATED":includestr,
		"KEY_MEDALS":html_medals,
		# tracks
		"KEY_TRACKLIST":html_tracks,
		# pulse
		"KEY_PULSE_MONTHS":html_pulse_months,
		"KEY_PULSE_YEARS":html_pulse_years,
		"KEY_PULSE_DAYS":html_pulse_days,
		"KEY_PULSE_WEEKS":html_pulse_weeks,
		# performance
		"KEY_PERFORMANCE_MONTHS":html_performance_months,
		"KEY_PERFORMANCE_YEARS":html_performance_years,
		"KEY_PERFORMANCE_DAYS":html_performance_days,
		"KEY_PERFORMANCE_WEEKS":html_performance_weeks,
		# scrobbles
		"KEY_SCROBBLELIST":html_scrobbles,
		"KEY_SCROBBLELINK":compose_querystring(keys),

	}

	return (replace,pushresources)
