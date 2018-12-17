import urllib
import json

		
def replacedict(keys,dbport):
	from utilities import getArtistInfo
	
	#hand down the since and from arguments
	extrakeys = urllib.parse.urlencode(keys)
	
	response = urllib.request.urlopen("http://localhost:" + str(dbport) + "/charts/artists?" + extrakeys)
	db_data = json.loads(response.read())
	charts = db_data["list"][:50]
	topartist = charts[0]["artist"]
	
	info = getArtistInfo(topartist)
	imgurl = info.get("image")
	
	
	response = urllib.request.urlopen("http://localhost:" + str(dbport) + "/scrobbles?" + extrakeys)
	db_data = json.loads(response.read())
	scrobblelist = db_data["list"]
	scrobbles = len(scrobblelist)
	
	
	
	
	html = "<table>"
	for e in charts:
		html += "<tr><td>"
		html += "<a href=/artist?artist=" + urllib.parse.quote(e["artist"]) + ">" + e["artist"] + "</a>"
		html += "</td><td>" + str(e["scrobbles"]) + "</td></tr>"
	html += "</table>"

	return {"KEY_TOPARTIST_IMAGEURL":imgurl,"KEY_SCROBBLES":str(scrobbles),"KEY_ARTISTLIST":html}

