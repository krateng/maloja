import urllib
import json

		
def replacedict(keys,dbport):
	from utilities import getArtistInfo, getTrackInfo
	from htmlgenerators import getTimeDesc, artistLink, artistLinks, trackLink, keysToUrl, pickKeys, clean
	
	clean(keys)
	timekeys = pickKeys(keys,"since","to","in","max")
	limitkeys = pickKeys(keys,"artist","title","associated")
	
	# Get scrobble data
	response = urllib.request.urlopen("http://[::1]:" + str(dbport) + "/scrobbles?" + keysToUrl(limitkeys,timekeys))
	db_data = json.loads(response.read())
	scrobbles = db_data["list"]
	
	# describe the scope
	limitstring = ""
	if keys.get("title") is not None:
		limitstring += "of " + trackLink({"title":keys.get("title"),"artists":keys.getall("artist")}) + " "
		limitstring += "by " + artistLinks(keys.getall("artist"))
	
	elif keys.get("artist") is not None:
		limitstring += "by " + artistLink(keys.get("artist"))
		if keys.get("associated") is not None:
			response = urllib.request.urlopen("http://[::1]:" + str(dbport) + "/artistinfo?artist=" + urllib.parse.quote(keys["artist"]))
			db_data = json.loads(response.read())
			moreartists = db_data["associated"]
			if moreartists != []:
				limitstring += " <span class='extra'>including " + artistLinks(moreartists) + "</span>"
		
	
	# get image	
	if limitkeys.get("title") is not None:
		imgurl = getTrackInfo(limitkeys.getall("artist"),limitkeys.get("title")).get("image")
	elif keys.get("artist") is not None:
		imgurl = getArtistInfo(keys.get("artist")).get("image")
	elif (len(scrobbles) != 0):
		imgurl = getTrackInfo(scrobbles[0]["artists"],scrobbles[0]["title"]).get("image")
		#imgurl = getArtistInfo(scrobbles[0]["artists"][0]).get("image")
	else:
		imgurl = ""
	

	# build list
	html = "<table class='list'>"
	for s in scrobbles:
		html += "<tr>"
		html += "<td class='time'>" + getTimeDesc(s["time"]) + "</td>"
		#html += """<td class='icon' style="background-image:url('""" + getArtistInfo(s["artists"][0]).get("image") + """')" /></td>"""
		html += "<td class='artists'>" + artistLinks(s["artists"]) + "</td>"
		html += "<td class='title'>" + trackLink({"artists":s["artists"],"title":s["title"]}) + "</td>"
		html += "</tr>"
	html += "</table>"
	
	return {"KEY_SCROBBLELIST":html,"KEY_SCROBBLES":str(len(scrobbles)),"KEY_IMAGEURL":imgurl,"KEY_LIMITS":limitstring}
		
