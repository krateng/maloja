import urllib
import json

		
def replacedict(keys,dbport):
	from utilities import getArtistInfo, getTimeDesc
	
	
	#hand down the since and from arguments
	extrakeys = urllib.parse.urlencode(keys)
	
	if keys.get("artist") is not None:
		info = getArtistInfo(keys.get("artist"))
		imgurl = info.get("image")
	else:
		imgurl = "" #for now
		
	limitstring = ""
	if keys.get("artist") is not None:
		limitstring += "by <a href='/artist?artist=" + urllib.parse.quote(keys.get("artist")) + "'>" + keys.get("artist") + "</a> "	
		
	
	response = urllib.request.urlopen("http://localhost:" + str(dbport) + "/scrobbles?" + extrakeys)
	db_data = json.loads(response.read())
	scrobbles = db_data["list"]
	
	html = "<table class='list'>"
	for s in scrobbles:
		html += "<tr><td class='time'>"
		timestring = getTimeDesc(s["time"])
		html += timestring
		html += "</td><td class='artists'>"
		artisthtml = ""
		for a in s["artists"]:
			artisthtml += "<a href=/artist?artist=" + urllib.parse.quote(a) + ">" + a + "</a>, "
		html += artisthtml[:-2]
		html += "</td><td class='title'>" + s["title"] + "</td></tr>"
	html += "</table>"
	
	return {"KEY_SCROBBLELIST":html,"KEY_SCROBBLES":str(len(scrobbles)),"KEY_IMAGEURL":imgurl,"KEY_LIMITS":limitstring}
		
