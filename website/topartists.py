import urllib
import json

		
def replacedict(keys,dbport):
	from utilities import getArtistInfo, artistLink
	
	#hand down the since and from arguments
	extrakeys = urllib.parse.urlencode(keys,quote_via=urllib.parse.quote,safe="/")
	
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
	
	
	maxbar = charts[0]["scrobbles"]
	
	i = 1
	html = "<table class='list'>"
	for e in charts:
		html += "<tr>"
		html += "<td class='rank'>#" + str(i) + "</td><td class='artist'>"
		#html += "<a href=/artist?artist=" + urllib.parse.quote(e["artist"]) + ">" + e["artist"] + "</a>"
		html += artistLink(e["artist"])
		if (e["counting"] != []):
			html += " <span class='extra'>incl. " + ", ".join([artistLink(a) for a in e["counting"]]) + "</span>"
		html += "</td><td class='amount'><a href='/scrobbles?artist=" + urllib.parse.quote(e["artist"]) + "&associated&" + extrakeys + "'>" + str(e["scrobbles"]) + "</a></td>"
		html += "<td class='bar'><a href='/scrobbles?artist=" + urllib.parse.quote(e["artist"]) + "&associated&" + extrakeys + "'><div style='width:" + str(e["scrobbles"]/maxbar * 100) + "%;'></div></a></td>"
		html += "</tr>"
		i += 1
	html += "</table>"

	return {"KEY_TOPARTIST_IMAGEURL":imgurl,"KEY_SCROBBLES":str(scrobbles),"KEY_ARTISTLIST":html}

