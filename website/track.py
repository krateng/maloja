import urllib
import json

		
def replacedict(keys,dbport):
	from utilities import getArtistInfo
	from htmlgenerators import clean, artistLink, artistLinks, trackLink, scrobblesTrackLink, keysToUrl, pickKeys, getTimeDesc

	clean(keys)
	limitkeys = pickKeys(keys,"artist","title")
	info = getArtistInfo(keys["artist"])
	imgurl = info.get("image")
	desc = info.get("info")
	
	response = urllib.request.urlopen("http://localhost:" + str(dbport) + "/trackinfo?" + keysToUrl(limitkeys))
	db_data = json.loads(response.read())
	scrobblesnum = str(db_data["scrobbles"])
	pos = "#" + str(db_data["position"])
	
	
	response = urllib.request.urlopen("http://localhost:" + str(dbport) + "/scrobbles?" + keysToUrl(limitkeys))
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
	

	return {"KEY_TRACKTITLE":limitkeys.get("title"),"KEY_ARTISTS":artistLinks(limitkeys.getall("artist")),"KEY_SCROBBLES":scrobblesnum,"KEY_IMAGEURL":imgurl,"KEY_SCROBBLELINK":keysToUrl(limitkeys),"KEY_SCROBBLELIST":html,"KEY_POSITION":pos}
