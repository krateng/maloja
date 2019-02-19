import urllib
import json

		
def instructions(keys,dbport):
	from utilities import getArtistInfo
	from htmlgenerators import clean, artistLink, artistLinks, trackLink, scrobblesTrackLink, getRangeDesc, scrobblesLink

	clean(keys)
	info = getArtistInfo(keys["artist"])
	imgurl = info.get("image")
	#desc = info.get("info")
	pushresources = [{"file":imgurl,"type":"image"}] if imgurl.startswith("/") else []
	
	response = urllib.request.urlopen("http://[::1]:" + str(dbport) + "/artistinfo?artist=" + urllib.parse.quote(keys["artist"]))
	db_data = json.loads(response.read())
	scrobbles = str(db_data["scrobbles"])
	pos = "#" + str(db_data["position"])
	
	credited = db_data.get("replace")
	includestr = " "
	if credited is not None:
		includestr = "Competing under " + artistLink(credited) + " (" + pos + ")"
		pos = ""
	included = db_data.get("associated")
	if included is not None and included != []:
		includestr = "associated: "
		includestr += artistLinks(included)
	
	
	
	
	response = urllib.request.urlopen("http://[::1]:" + str(dbport) + "/charts/tracks?artist=" + urllib.parse.quote(keys["artist"]))
	db_data = json.loads(response.read())
	
	if db_data["list"] != []: maxbar = db_data["list"][0]["scrobbles"]
	html = "<table class='list'>"
	for e in db_data["list"]:
		html += "<tr>"
		html += "<td class='artists'>" + artistLinks(e["track"]["artists"]) + "</td>"
		html += "<td>" + trackLink(e["track"]) + "</td>"
		html += "<td class='amount'>" + scrobblesTrackLink(e["track"],{},amount=e["scrobbles"]) + "</td>"
		html += "<td class='bar'>" + scrobblesTrackLink(e["track"],{},percent=e["scrobbles"]*100/maxbar) + "</td>"
		html += "</tr>"
	html += "</table>"
	
	
	# pulse
	response = urllib.request.urlopen("http://[::1]:" + str(dbport) + "/pulse?step=year&trail=1&artist=" + urllib.parse.quote(keys["artist"]))
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
		html_pulse += "<td class='amount'>" + scrobblesLink({"since":fromstr,"to":tostr},amount=t["scrobbles"],artist=keys["artist"]) + "</td>"
		html_pulse += "<td class='bar'>" + scrobblesLink({"since":fromstr,"to":tostr},percent=t["scrobbles"]*100/maxbar,artist=keys["artist"]) + "</td>"
		html_pulse += "</tr>"
	html_pulse += "</table>"
	
	

	replace = {"KEY_ARTISTNAME":keys["artist"],"KEY_ENC_ARTISTNAME":urllib.parse.quote(keys["artist"]),"KEY_IMAGEURL":imgurl, "KEY_DESCRIPTION":"","KEY_TRACKLIST":html,"KEY_SCROBBLES":scrobbles,"KEY_POSITION":pos,"KEY_ASSOCIATED":includestr,"KEY_PULSE":html_pulse}
	
	return (replace,pushresources)
