import urllib
import json

		
def replacedict(keys,dbport):
	from utilities import getArtistInfo
	from htmlgenerators import artistLink, keysToUrl, pickKeys
	
	timekeys = pickKeys(keys,"since","to","in")
	limitkeys = pickKeys(keys,"artist")
	
	response = urllib.request.urlopen("http://localhost:" + str(dbport) + "/charts/tracks?" + keysToUrl(timekeys,limitkeys))
	db_data = json.loads(response.read())
	charts = db_data["list"][:50]
	limitstring = ""
	
	if keys.get("artist") is not None:
		topartist = keys.get("artist")
		#limitstring += "by " + ", ".join([artistLink(a) for a in keys.getall("artist")])
		limitstring = "by " + artistLink(keys.get("artist"))
	else:
		topartist = charts[0]["track"]["artists"][0] #for now
	
	info = getArtistInfo(topartist)
	imgurl = info.get("image")
	
	
	response = urllib.request.urlopen("http://localhost:" + str(dbport) + "/scrobbles?" + keysToUrl(timekeys,limitkeys))
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
		html += "</td><td class='amount'><a href='/scrobbles?" + "&".join(["artist=" + urllib.parse.quote(a) for a in e["track"]["artists"]]) + "&title=" + urllib.parse.quote(e["track"]["title"]) + "&" + keysToUrl(timekeys) + "'>" + str(e["scrobbles"]) + "</a></td>"
		html += "<td class='bar'><a href='/scrobbles?" + "&".join(["artist=" + urllib.parse.quote(a) for a in e["track"]["artists"]]) + "&title=" + urllib.parse.quote(e["track"]["title"]) + "&" + keysToUrl(timekeys) + "'><div style='width:" + str(e["scrobbles"]/maxbar * 100) + "%;'></div></a>"
		html += "</td>"
		html += "</tr>"
		i += 1
	html += "</table>"

	return {"KEY_TOPARTIST_IMAGEURL":imgurl,"KEY_SCROBBLES":str(scrobbles),"KEY_TRACKLIST":html,"KEY_LIMITS":limitstring}

