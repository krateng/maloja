import urllib
import json

		
def instructions(keys,dbport):
	from utilities import getArtistInfo, getTrackInfo
	from htmlgenerators import getTimeDesc, artistLink, artistLinks, trackLink, keysToUrl, KeySplit
	from htmlmodules import module_scrobblelist
	
	
	filterkeys, timekeys, _, amountkeys = KeySplit(keys)
	
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
		

	
	html, amount, rep = module_scrobblelist(**filterkeys,**timekeys,**amountkeys)
	
	# get image	
	if filterkeys.get("track") is not None:
		imgurl = getTrackInfo(filterkeys.get("track")["artists"],filterkeys.get("track")["title"]).get("image")
	elif filterkeys.get("artist") is not None:
		imgurl = getArtistInfo(keys.get("artist")).get("image")
	elif rep is not None:
		imgurl = getTrackInfo(rep["artists"],rep["title"]).get("image")
	else:
		imgurl = ""
	
		
	pushresources = [{"file":imgurl,"type":"image"}] if imgurl.startswith("/") else []

	
	replace = {"KEY_SCROBBLELIST":html,"KEY_SCROBBLES":str(amount),"KEY_IMAGEURL":imgurl,"KEY_LIMITS":limitstring}
	
	return (replace,pushresources)
		
