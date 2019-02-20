import urllib
import json

		
def instructions(keys,dbport):
	from utilities import getArtistInfo, getTrackInfo
	from htmlgenerators import artistLink, KeySplit
	from htmlmodules import module_trackcharts
	
#	clean(keys)
#	timekeys = pickKeys(keys,"since","to","in")
#	limitkeys = pickKeys(keys,"artist")
	
	filterkeys, timekeys, _, amountkeys = KeySplit(keys)
	

	limitstring = ""
	
	if filterkeys.get("artist") is not None:
		topartist = filterkeys.get("artist")
#		#limitstring += "by " + ", ".join([artistLink(a) for a in keys.getall("artist")])
		limitstring = "by " + artistLink(filterkeys.get("artist"))
#		info = getArtistInfo(topartist)
#		imgurl = info.get("image")
#	else:
#		#topartist = charts[0]["track"]["artists"][0] #for now
#		info = getTrackInfo(charts[0]["track"]["artists"],charts[0]["track"]["title"])
#		imgurl = info.get("image")

	
	
	
	
	# get total amount of scrobbles
#	response = urllib.request.urlopen("http://[::1]:" + str(dbport) + "/scrobbles?" + keysToUrl(timekeys,limitkeys))
#	db_data = json.loads(response.read())
#	scrobblelist = db_data["list"]
#	scrobbles = len(scrobblelist)
	
	
	html_charts, rep = module_trackcharts(**amountkeys,**timekeys,**filterkeys)
	
	
	if filterkeys.get("artist") is not None:
		imgurl = getArtistInfo(filterkeys.get("artist")).get("image")
		limitstring = "by " + artistLink(filterkeys.get("artist"))
	elif rep is not None:
		imgurl = getTrackInfo(rep["artists"],rep["title"]).get("image")		
	else:
		imgurl = ""
	
	pushresources = [{"file":imgurl,"type":"image"}] if imgurl.startswith("/") else []
	
	# build list
#	maxbar = charts[0]["scrobbles"]
#	
#	i = 1
#	html = "<table class='list'>"
#	for e in charts:
#		html += "<tr>"
#		html += "<td class='rank'>#" + str(i) + "</td>"
#		html += "<td class='artists'>" + artistLinks(e["track"]["artists"]) + "</td>"
#		html += "<td class='title'>" + trackLink(e["track"]) + "</td>"
#		html += "<td class='amount'>" + scrobblesTrackLink(e["track"],timekeys,amount=e["scrobbles"]) + "</td>"
#		html += "<td class='bar'>" + scrobblesTrackLink(e["track"],timekeys,percent=e["scrobbles"]*100/maxbar) + "</td>"
#		html += "</tr>"
#		i += 1
#	html += "</table>"

	replace = {"KEY_TOPARTIST_IMAGEURL":imgurl,"KEY_TRACKLIST":html_charts,"KEY_LIMITS":limitstring}
	
	return (replace,pushresources)

