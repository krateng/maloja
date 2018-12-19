import urllib
import json

		
def replacedict(keys,dbport):
	from utilities import getArtistInfo

	
	info = getArtistInfo(keys["artist"])
	imgurl = info.get("image")
	desc = info.get("info")
	
	response = urllib.request.urlopen("http://localhost:" + str(dbport) + "/artistinfo?artist=" + urllib.parse.quote(keys["artist"]))
	db_data = json.loads(response.read())
	scrobbles = str(db_data["scrobbles"])
	pos = "#" + str(db_data["position"])
	
	credited = db_data.get("replace")
	includestr = " "
	if credited is not None:
		includestr = "Competing under <a href=/artist?artist=" + urllib.parse.quote(credited) + ">" + credited + "</a> (" + pos + ")"
		pos = ""
	included = db_data.get("associated")
	if included is not None and included != []:
		includestr = "associated: "
		for a in included:
			includestr += "<a href=/artist?artist=" + urllib.parse.quote(a) + ">" + a + "</a>, "
		includestr = includestr[:-2]
	
	response = urllib.request.urlopen("http://localhost:" + str(dbport) + "/tracks?artist=" + urllib.parse.quote(keys["artist"]))
	db_data = json.loads(response.read())
	tracks = []
	for e in db_data["list"]:
		html = "<td class='artists'>"
		for a in e["artists"]:
			html += "<a href=/artist?artist=" + urllib.parse.quote(a) + ">" + a + "</a>, "
		html = html[:-2]
		html += "</td><td class='title'>" + e["title"] + "</td>"
		tracks.append(html)
	
	trackshtml = "<table>"	
	for t in tracks:
		trackshtml += "<tr>"
		trackshtml += t
		trackshtml += "</tr>"
	trackshtml += "</table>"
	

	return {"KEY_ARTISTNAME":keys["artist"],"KEY_ENC_ARTISTNAME":urllib.parse.quote(keys["artist"]),"KEY_IMAGEURL":imgurl, "KEY_DESCRIPTION":desc,"KEY_TRACKLIST":trackshtml,"KEY_SCROBBLES":scrobbles,"KEY_POSITION":pos,"KEY_ASSOCIATED":includestr}
