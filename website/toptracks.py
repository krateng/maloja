import urllib
import json

		
def replacedict(keys,dbport):
	from utilities import getArtistInfo, getTrackInfo
	from htmlgenerators import artistLink, artistLinks, trackLink, scrobblesTrackLink, keysToUrl, pickKeys, clean
	
	clean(keys)
	timekeys = pickKeys(keys,"since","to","in")
	limitkeys = pickKeys(keys,"artist")
	
	# get chart data
	response = urllib.request.urlopen("http://[::1]:" + str(dbport) + "/charts/tracks?" + keysToUrl(timekeys,limitkeys))
	db_data = json.loads(response.read())
	charts = db_data["list"][:50]
	limitstring = ""
	
	if keys.get("artist") is not None:
		topartist = keys.get("artist")
		#limitstring += "by " + ", ".join([artistLink(a) for a in keys.getall("artist")])
		limitstring = "by " + artistLink(keys.get("artist"))
		info = getArtistInfo(topartist)
		imgurl = info.get("image")
	else:
		#topartist = charts[0]["track"]["artists"][0] #for now
		info = getTrackInfo(charts[0]["track"]["artists"],charts[0]["track"]["title"])
		imgurl = info.get("image")
	
	
	
	# get total amount of scrobbles
	response = urllib.request.urlopen("http://[::1]:" + str(dbport) + "/scrobbles?" + keysToUrl(timekeys,limitkeys))
	db_data = json.loads(response.read())
	scrobblelist = db_data["list"]
	scrobbles = len(scrobblelist)
	
	
	# build list
	maxbar = charts[0]["scrobbles"]
	
	i = 1
	html = "<table class='list'>"
	for e in charts:
		html += "<tr>"
		html += "<td class='rank'>#" + str(i) + "</td>"
		html += "<td class='artists'>" + artistLinks(e["track"]["artists"]) + "</td>"
		html += "<td class='title'>" + trackLink(e["track"]) + "</td>"
		html += "<td class='amount'>" + scrobblesTrackLink(e["track"],timekeys,amount=e["scrobbles"]) + "</td>"
		html += "<td class='bar'>" + scrobblesTrackLink(e["track"],timekeys,percent=e["scrobbles"]*100/maxbar) + "</td>"
		html += "</tr>"
		i += 1
	html += "</table>"

	return {"KEY_TOPARTIST_IMAGEURL":imgurl,"KEY_SCROBBLES":str(scrobbles),"KEY_TRACKLIST":html,"KEY_LIMITS":limitstring}

