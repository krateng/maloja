import urllib
from .. import database
from ..malojatime import today,thisweek,thismonth,thisyear


def instructions(keys):
	from ..utilities import getArtistImage, getTrackImage
	from ..htmlgenerators import artistLinks
	from ..urihandler import compose_querystring, uri_to_internal
	from ..htmlmodules import module_scrobblelist, module_pulse, module_performance


	filterkeys, _, _, _ = uri_to_internal(keys,forceTrack=True)

	track = filterkeys.get("track")
	imgurl = getTrackImage(track["artists"],track["title"],fast=True)
	pushresources = [{"file":imgurl,"type":"image"}] if imgurl.startswith("/") else []

	data = database.trackInfo(track)

	scrobblesnum = str(data["scrobbles"])
	pos = "#" + str(data["position"])

	html_cert = ""
	if data["certification"] is not None:
		html_cert = "<img class='certrecord' src='/media/record_{cert}.png' title='This track has reached {certc} status' />".format(cert=data["certification"],certc=data["certification"].capitalize())

	html_medals = ""
	if "medals" in data and data["medals"] is not None:
		if "gold" in data["medals"]:
			for y in data["medals"]["gold"]:
				html_medals += "<a  title='Best Track in " + str(y) + "' class='hidelink medal shiny gold' href='/charts_tracks?in=" + str(y) + "'><span>" + str(y) + "</span></a>"
		if "silver" in data["medals"]:
			for y in data["medals"]["silver"]:
				html_medals += "<a title='Second Best Track in " + str(y) + "' class='hidelink medal shiny silver' href='/charts_tracks?in=" + str(y) + "'><span>" + str(y) + "</span></a>"
		if "bronze" in data["medals"]:
			for y in data["medals"]["bronze"]:
				html_medals += "<a title='Third Best Track in " + str(y) + "' class='hidelink medal shiny bronze' href='/charts_tracks?in=" + str(y) + "'><span>" + str(y) + "</span></a>"

	html_topweeks = ""
	if data.get("topweeks") not in [0,None]:
		link = "/performance?" + compose_querystring(keys) + "&trail=1&step=week"
		title = str(data["topweeks"]) + " weeks on #1"
		html_topweeks = "<a title='" + title + "' href='" + link + "'><img class='star' src='/media/star.png' />" + str(data["topweeks"]) + "</a>"



	html_scrobbles, _, _ = module_scrobblelist(track=track,max_=10,earlystop=True)	 # we have the number already from the trackinfo

	html_pulse = module_pulse(track=track,step="year",stepn=1,trail=1)
	html_performance = module_performance(track=track,step="year",stepn=1,trail=1)

	# pulse and rankings
	html_pulse_days = module_pulse(track=track,max_=7,since=today().next(-6),step="day",trail=1)
	html_pulse_weeks = module_pulse(track=track,max_=12,since=thisweek().next(-11),step="week",trail=1)
	html_pulse_months = module_pulse(track=track,max_=12,since=thismonth().next(-11),step="month",trail=1)
	html_pulse_years = module_pulse(track=track,max_=10,since=thisyear().next(-9),step="year",trail=1)

	html_performance_days = module_performance(track=track,max_=7,since=today().next(-6),step="day",trail=1)
	html_performance_weeks = module_performance(track=track,max_=12,since=thisweek().next(-11),step="week",trail=1)
	html_performance_months = module_performance(track=track,max_=12,since=thismonth().next(-11),step="month",trail=1)
	html_performance_years = module_performance(track=track,max_=10,since=thisyear().next(-9),step="year",trail=1)


	replace = {
		"KEY_TRACKTITLE":track.get("title"),
		"KEY_ARTISTS":artistLinks(track.get("artists")),
		"KEY_SCROBBLES":scrobblesnum,
		"KEY_POSITION":pos,
		"KEY_IMAGEURL":imgurl,
		"KEY_SCROBBLELINK":compose_querystring(keys),
		"KEY_MEDALS":html_medals,
		"KEY_CERTS":html_cert,
		"KEY_TOPWEEKS":html_topweeks,
		"KEY_SCROBBLELIST":html_scrobbles,
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
	}

	return (replace,pushresources)
