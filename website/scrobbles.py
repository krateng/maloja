import urllib
import json

		
def replacedict(keys,dbport):
	from utilities import getArtistInfo
	from htmlgenerators import getTimeDesc, artistLink, keysToUrl, pickKeys
	
	timekeys = pickKeys(keys,"since","to","in")
	limitkeys = pickKeys(keys,"artist","title")

	limitstring = ""
	
	response = urllib.request.urlopen("http://localhost:" + str(dbport) + "/scrobbles?" + keysToUrl(limitkeys,timekeys))
	db_data = json.loads(response.read())
	scrobbles = db_data["list"]
	
	if keys.get("title") is not None:
		limitstring += "of " + keys.get("title") + " "
		limitstring += "by " + ", ".join([artistLink(a) for a in keys.getall("artist")])
		latestartist = keys.get("artist")
	
	elif keys.get("artist") is not None:
		latestartist = keys.get("artist")
		limitstring += "by " + artistLink(keys.get("artist")) #if we dont specifiy a title, we filter by one artist, which means only one artist is allowed
		if keys.get("associated") is not None:
			response = urllib.request.urlopen("http://localhost:" + str(dbport) + "/artistinfo?artist=" + urllib.parse.quote(keys["artist"]))
			db_data = json.loads(response.read())
			moreartists = [artistLink(a) for a in db_data["associated"]]
			if moreartists != []:
				limitstring += " <span class='extra'>including " + ", ".join(moreartists) + "</span>"
		
	else:
		latestartist = scrobbles[0]["artists"][0]
	
	info = getArtistInfo(latestartist)
	imgurl = info.get("image")

	html = "<table class='list'>"
	for s in scrobbles:
		html += "<tr><td class='time'>"
		timestring = getTimeDesc(s["time"])
		html += timestring
		html += "</td><td class='artists'>"
		html += ", ".join([artistLink(a) for a in s["artists"]])
		#artisthtml = ""
		#for a in s["artists"]:
		#	artisthtml += "<a href=/artist?artist=" + urllib.parse.quote(a) + ">" + a + "</a>, "
		#html += artisthtml[:-2]
		html += "</td><td class='title'>" + s["title"] + "</td></tr>"
	html += "</table>"
	
	return {"KEY_SCROBBLELIST":html,"KEY_SCROBBLES":str(len(scrobbles)),"KEY_IMAGEURL":imgurl,"KEY_LIMITS":limitstring}
		
