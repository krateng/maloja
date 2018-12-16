import urllib
import json



#def page(keys):
#
#	txt_keys = replace(keys)
#
#
#	with open("website/artist.html","r") as htmlfile:
#		html = htmlfile.read()
#			
#		
#
#		for k in txt_keys:
#			html = html.replace(k,txt_keys[k])
#			
#		return html
		
def replacedict(keys,dbport):

	with open("website/apikey","r") as keyfile:
		apikey = keyfile.read().replace("\n","")
	
	
	url = "https://ws.audioscrobbler.com/2.0/?method=artist.getinfo&artist=" + urllib.parse.quote(keys["artist"]) + "&api_key=" + apikey + "&format=json"
	response = urllib.request.urlopen(url)
	lastfm_data = json.loads(response.read())
	imgurl = lastfm_data["artist"]["image"][2]["#text"]
	desc = lastfm_data["artist"]["bio"]["summary"]
	
	response = urllib.request.urlopen("http://localhost:" + str(dbport) + "/artistinfo?artist=" + urllib.parse.quote(keys["artist"]))
	db_data = json.loads(response.read())
	scrobbles = str(db_data["scrobbles"])
	pos = "#" + str(db_data["position"])
	credited = db_data.get("replace")
	includestr = " "
	if credited is not None:
		includestr = "Competing under <a href=/artist?artist=" + urllib.parse.quote(credited) + ">" + credited + "</a> (" + pos + ")"
		pos = ""
	included = db_data.get("associated")
	if included is not None and included != []:
		includestr = "associated: "
		for a in included:
			includestr += "<a href=/artist?artist=" + urllib.parse.quote(a) + ">" + a + "</a>, "
		includestr = includestr[:-2]
	
	response = urllib.request.urlopen("http://localhost:" + str(dbport) + "/tracks?artist=" + urllib.parse.quote(keys["artist"]))
	db_data = json.loads(response.read())
	tracks = []
	for e in db_data["list"]:
		html = "<td>"
		for a in e["artists"]:
			html += "<a href=/artist?artist=" + urllib.parse.quote(a) + ">" + a + "</a>, "
		html = html[:-2]
		html += "</td><td>" + e["title"] + "</td>"
		tracks.append(html)
	
	trackshtml = "<table>"	
	for t in tracks:
		trackshtml += "<tr>"
		trackshtml += t
		trackshtml += "</tr>"
	trackshtml += "</table>"
	

	return {"KEY_ARTISTNAME":keys["artist"],"KEY_IMAGEURL":imgurl,"KEY_DESCRIPTION":desc,"KEY_TRACKLIST":trackshtml,"KEY_SCROBBLES":scrobbles,"KEY_POSITION":pos,"KEY_ASSOCIATED":includestr}
