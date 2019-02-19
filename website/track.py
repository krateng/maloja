import urllib
import json

		
def instructions(keys,dbport):
	from utilities import getArtistInfo, getTrackInfo
	from htmlgenerators import clean, artistLink, artistLinks, trackLink, scrobblesTrackLink, keysToUrl, pickKeys, getTimeDesc, getRangeDesc, scrobblesLink

	clean(keys)
	limitkeys = pickKeys(keys,"artist","title")
	trackobject = {"artists":limitkeys.getall("artist"),"title":limitkeys.get("title")}
	info = getTrackInfo(keys.getall("artist"),keys.get("title"))
	imgurl = info.get("image")
	pushresources = [{"file":imgurl,"type":"image"}] if imgurl.startswith("/") else []
	
	response = urllib.request.urlopen("http://[::1]:" + str(dbport) + "/trackinfo?" + keysToUrl(limitkeys))
	db_data = json.loads(response.read())
	scrobblesnum = str(db_data["scrobbles"])
	pos = "#" + str(db_data["position"])
	
	
	response = urllib.request.urlopen("http://[::1]:" + str(dbport) + "/scrobbles?" + keysToUrl(limitkeys))
	db_data = json.loads(response.read())
	scrobbles = db_data["list"]
	
	
	# build list
	html = "<table class='list'>"
	for s in scrobbles:
		html += "<tr>"
		html += "<td class='time'>" + getTimeDesc(s["time"]) + "</td>"
		html += "<td class='artists'>" + artistLinks(s["artists"]) + "</td>"
		html += "<td class='title'>" + trackLink({"artists":s["artists"],"title":s["title"]}) + "</td>"
		html += "</tr>"
	html += "</table>"
	
	
	# pulse
	response = urllib.request.urlopen("http://[::1]:" + str(dbport) + "/pulse?step=year&trail=1&" + keysToUrl(limitkeys))
	db_data = json.loads(response.read())
	terms = db_data["list"]
	
	# build list
	maxbar = max([t["scrobbles"] for t in terms])
	
	html_pulse = "<table class='list'>"
	for t in terms:
		fromstr = "/".join([str(e) for e in t["from"]])
		tostr = "/".join([str(e) for e in t["to"]])
		html_pulse += "<tr>"
		#html += "<td>" + fromstr + "</td>"
		#html += "<td>" + tostr + "</td>"
		html_pulse += "<td>" + getRangeDesc(t["from"],t["to"]) + "</td>"
		html_pulse += "<td class='amount'>" + scrobblesLink({"since":fromstr,"to":tostr},amount=t["scrobbles"],track=trackobject) + "</td>"
		html_pulse += "<td class='bar'>" + scrobblesLink({"since":fromstr,"to":tostr},percent=t["scrobbles"]*100/maxbar,track=trackobject) + "</td>"
		html_pulse += "</tr>"
	html_pulse += "</table>"
	

	replace = {"KEY_TRACKTITLE":limitkeys.get("title"),"KEY_ARTISTS":artistLinks(limitkeys.getall("artist")),"KEY_SCROBBLES":scrobblesnum,"KEY_IMAGEURL":imgurl,
		"KEY_SCROBBLELINK":keysToUrl(limitkeys),"KEY_SCROBBLELIST":html,"KEY_POSITION":pos,"KEY_PULSE":html_pulse}
	
	return (replace,pushresources)
