import urllib
import json



def page(keys):

	txt_keys = replace(keys)


	with open("website/artist.html","r") as htmlfile:
		html = htmlfile.read()
			
		

		for k in txt_keys:
			html = html.replace(k,txt_keys[k])
			
		return html
		
def replace(keys):
	with open("website/apikey","r") as keyfile:
		apikey = keyfile.read().replace("\n","")
	url = "https://ws.audioscrobbler.com/2.0/?method=artist.getinfo&artist=" + keys["artist"] + "&api_key=" + apikey + "&format=json"
	response = urllib.request.urlopen(url)
	lastfm_data = json.loads(response.read())
	imgurl = lastfm_data["artist"]["image"][2]["#text"]
	desc = lastfm_data["artist"]["bio"]["summary"]
	
	response = urllib.request.urlopen("http://localhost:42010/db/tracks?artist=" + urllib.parse.quote(keys["artist"]))
	db_data = json.loads(response.read())
	tracks = []
	for e in db_data["list"]:
		html = "<td>"
		for a in e["artists"]:
			html += "<a href=/artist?artist=" + urllib.parse.quote(a) + ">" + a + "</a> "
		html += "</td><td>" + e["title"] + "</td>"
		tracks.append(html)
	
	trackshtml = "<table>"	
	for t in tracks:
		trackshtml += "<tr>"
		trackshtml += t
		trackshtml += "</tr>"
	trackshtml += "</table>"
	

	return {"KEY_ARTISTNAME":keys["artist"],"KEY_IMAGEURL":imgurl,"KEY_DESCRIPTION":desc,"KEY_TRACKLIST":trackshtml}
