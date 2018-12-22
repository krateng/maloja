import urllib
import json

		
def replacedict(keys,dbport):
	from utilities import getArtistInfo, artistLink

	
	info = getArtistInfo(keys["artist"])
	imgurl = info.get("image")
	desc = info.get("info")
	
	response = urllib.request.urlopen("http://localhost:" + str(dbport) + "/artistinfo?artist=" + urllib.parse.quote(keys["artist"]))
	db_data = json.loads(response.read())
	scrobbles = str(db_data["scrobbles"])
	pos = "#" + str(db_data["position"])
	
	credited = db_data.get("replace")
	includestr = " "
	if credited is not None:
		includestr = "Competing under " + artistLink(credited) + " (" + pos + ")"
		pos = ""
	included = db_data.get("associated")
	if included is not None and included != []:
		includestr = "associated: "
		#for a in included:
		includestr += ", ".join([artistLink(a) for a in included]) #"<a href=/artist?artist=" + urllib.parse.quote(a) + ">" + a + "</a>, "
		#includestr = includestr[:-2]
	
#	response = urllib.request.urlopen("http://localhost:" + str(dbport) + "/tracks?artist=" + urllib.parse.quote(keys["artist"]))
#	db_data = json.loads(response.read())
#	
#	html = "<table class='list'>"
#	for e in db_data["list"]:
#		html += "<tr>"
#		html += "<td class='artists'>"
#		links = [artistLink(a) for a in e["artists"]]
#		html += ", ".join(links)
#		html += "</td><td class='title'>" + e["title"] + "</td>"
#		html += "</tr>"
#	html += "</table>"
	
	
	
	
	response = urllib.request.urlopen("http://localhost:" + str(dbport) + "/charts/tracks?artist=" + urllib.parse.quote(keys["artist"]))
	db_data = json.loads(response.read())
	
	maxbar = db_data["list"][0]["scrobbles"]
	html = "<table class='list'>"
	for e in db_data["list"]:
		html += "<tr>"
		html += "<td class='artists'>"
		links = [artistLink(a) for a in e["track"]["artists"]]
		html += ", ".join(links)
		html += "</td><td class='title'>" + e["track"]["title"] + "</td>"
		html += "</td><td class='amount'>" + str(e["scrobbles"]) + "</td>"
		html += "<td class='bar'><div style='width:" + str(e["scrobbles"]/maxbar * 100) + "%;'></div></td>"
		html += "</tr>"
	html += "</table>"
	

	return {"KEY_ARTISTNAME":keys["artist"],"KEY_ENC_ARTISTNAME":urllib.parse.quote(keys["artist"]),"KEY_IMAGEURL":imgurl, "KEY_DESCRIPTION":desc,"KEY_TRACKLIST":html,"KEY_SCROBBLES":scrobbles,"KEY_POSITION":pos,"KEY_ASSOCIATED":includestr}
