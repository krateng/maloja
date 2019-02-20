import urllib
import database

		
def instructions(keys,dbport):
	from utilities import getArtistInfo, getTrackInfo
	from htmlgenerators import clean, artistLink, artistLinks, trackLink, scrobblesTrackLink, keysToUrl, pickKeys, getTimeDesc, getRangeDesc, scrobblesLink, KeySplit
	from htmlmodules import module_scrobblelist, module_pulse

	
	filterkeys, _, _, _ = KeySplit(keys,forceTrack=True)	
	
	track = filterkeys.get("track")
	imgurl = getTrackInfo(track["artists"],track["title"]).get("image")
	pushresources = [{"file":imgurl,"type":"image"}] if imgurl.startswith("/") else []
	
	data = database.trackInfo(track["artists"],track["title"])
	scrobblesnum = str(data["scrobbles"])
	pos = "#" + str(data["position"])
	
	
	#response = urllib.request.urlopen("http://[::1]:" + str(dbport) + "/scrobbles?" + keysToUrl(limitkeys))
	#db_data = json.loads(response.read())
	#scrobbles = db_data["list"]
	
	
	# build list
#	html = "<table class='list'>"
#	for s in scrobbles:
#		html += "<tr>"
#		html += "<td class='time'>" + getTimeDesc(s["time"]) + "</td>"
#		html += "<td class='artists'>" + artistLinks(s["artists"]) + "</td>"
#		html += "<td class='title'>" + trackLink({"artists":s["artists"],"title":s["title"]}) + "</td>"
#		html += "</tr>"
#	html += "</table>"

	html_scrobbles, _, _ = module_scrobblelist(track=track,max_=100)	
	
	# pulse
#	response = urllib.request.urlopen("http://[::1]:" + str(dbport) + "/pulse?step=year&trail=1&" + keysToUrl(limitkeys))
#	db_data = json.loads(response.read())
#	terms = db_data["list"]
	
	# build list
#	maxbar = max([t["scrobbles"] for t in terms])
	
#	html_pulse = "<table class='list'>"
#	for t in terms:
#		fromstr = "/".join([str(e) for e in t["from"]])
#		tostr = "/".join([str(e) for e in t["to"]])
#		html_pulse += "<tr>"
#		#html += "<td>" + fromstr + "</td>"
#		#html += "<td>" + tostr + "</td>"
#		html_pulse += "<td>" + getRangeDesc(t["from"],t["to"]) + "</td>"
#		html_pulse += "<td class='amount'>" + scrobblesLink({"since":fromstr,"to":tostr},amount=t["scrobbles"],track=trackobject) + "</td>"
#		html_pulse += "<td class='bar'>" + scrobblesLink({"since":fromstr,"to":tostr},percent=t["scrobbles"]*100/maxbar,track=trackobject) + "</td>"
#		html_pulse += "</tr>"
#	html_pulse += "</table>"
	
	html_pulse = module_pulse(track=track,step="year",stepn=1,trail=1)


	replace = {"KEY_TRACKTITLE":track.get("title"),"KEY_ARTISTS":artistLinks(track.get("artists")),"KEY_SCROBBLES":scrobblesnum,"KEY_POSITION":pos,"KEY_IMAGEURL":imgurl,
		"KEY_SCROBBLELINK":keysToUrl(keys),
		"KEY_SCROBBLELIST":html_scrobbles,"KEY_PULSE":html_pulse}
	
	return (replace,pushresources)
