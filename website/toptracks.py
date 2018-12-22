import urllib
import json

		
def replacedict(keys,dbport):
	from utilities import getArtistInfo, artistLink
	
	# we don't use the associated key for top tracks so we don't wanna hand it down to functions we're calling
	keys.pop("associated",None)
	
	#hand down the since and from arguments
	extrakeys = urllib.parse.urlencode(keys,quote_via=urllib.parse.quote,safe="/")
	
	response = urllib.request.urlopen("http://localhost:" + str(dbport) + "/charts/tracks?" + extrakeys)
	db_data = json.loads(response.read())
	charts = db_data["list"][:50]
	limitstring = ""
	
	if keys.get("artist") is not None:
		topartist = keys.get("artist")
		limitstring += "by " + artistLink(keys.get("artist"))
		
	else:
		topartist = charts[0]["track"]["artists"][0] #for now
	
	info = getArtistInfo(topartist)
	imgurl = info.get("image")
	
	
	response = urllib.request.urlopen("http://localhost:" + str(dbport) + "/scrobbles?" + extrakeys)
	db_data = json.loads(response.read())
	scrobblelist = db_data["list"]
	scrobbles = len(scrobblelist)
	
	
	maxbar = charts[0]["scrobbles"]
	
	i = 1
	html = "<table class='list'>"
	for e in charts:
		html += "<tr>"
		html += "<td class='rank'>#" + str(i) + "</td><td class='artists'>"
		html += ", ".join([artistLink(a) for a in e["track"]["artists"]])
		html += "</td><td class='title'>" + e["track"]["title"]
		html += "</td><td class='amount'>" + str(e["scrobbles"]) + "</td>"
		html += "<td class='bar'><div style='width:" + str(e["scrobbles"]/maxbar * 100) + "%;'></div>"
		html += "</td>"
		html += "</tr>"
		i += 1
	html += "</table>"

	return {"KEY_TOPARTIST_IMAGEURL":imgurl,"KEY_SCROBBLES":str(scrobbles),"KEY_TRACKLIST":html,"KEY_LIMITS":limitstring}

