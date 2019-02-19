import urllib
import json

		
def instructions(keys,dbport):
	from utilities import getArtistInfo, getTrackInfo
	from htmlgenerators import getTimeDesc, artistLink, artistLinks, trackLink, scrobblesLink, keysToUrl, pickKeys, clean, getRangeDesc
	
	clean(keys)
	timekeys = pickKeys(keys,"since","to","in","step","trail")
	limitkeys = pickKeys(keys,"artist","title","associated")
	
	# Get scrobble data
	response = urllib.request.urlopen("http://[::1]:" + str(dbport) + "/pulse?" + keysToUrl(limitkeys,timekeys))
	db_data = json.loads(response.read())
	terms = db_data["list"]
	
	# describe the scope (and creating a key for the relevant artist or track)
	limitstring = ""
	limitkey = {}
	if keys.get("title") is not None:
		limitkey["track"] = {"artists":keys.getall("artist"),"title":keys.get("title")}
		limitstring += "of " + trackLink(limitkey["track"]) + " "
		limitstring += "by " + artistLinks(keys.getall("artist"))
	
	elif keys.get("artist") is not None:
		limitkey["artist"], limitkey["associated"] = keys.get("artist"), (keys.get("associated")!=None)
		limitstring += "of " + artistLink(keys.get("artist"))
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
	#elif (len(scrobbles) != 0):
	#	imgurl = getTrackInfo(scrobbles[0]["artists"],scrobbles[0]["title"]).get("image")
	#	#imgurl = getArtistInfo(scrobbles[0]["artists"][0]).get("image")
	else:
		imgurl = ""
		
	pushresources = [{"file":imgurl,"type":"image"}] if imgurl.startswith("/") else []
	

	
	# build list
	maxbar = max([t["scrobbles"] for t in terms])
	
	html = "<table class='list'>"
	for t in terms:
		fromstr = "/".join([str(e) for e in t["from"]])
		tostr = "/".join([str(e) for e in t["to"]])
		html += "<tr>"
		#html += "<td>" + fromstr + "</td>"
		#html += "<td>" + tostr + "</td>"
		html += "<td>" + getRangeDesc(t["from"],t["to"]) + "</td>"
		html += "<td class='amount'>" + scrobblesLink({"since":fromstr,"to":tostr},amount=t["scrobbles"],**limitkey) + "</td>"
		html += "<td class='bar'>" + scrobblesLink({"since":fromstr,"to":tostr},percent=t["scrobbles"]*100/maxbar,**limitkey) + "</td>"
		html += "</tr>"
	html += "</table>"
	
	replace = {"KEY_PULSE_TABLE":html,"KEY_IMAGEURL":imgurl,"KEY_LIMITS":limitstring}
	
	return (replace,pushresources)
		
