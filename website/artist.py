import urllib
import json

		
def instructions(keys,dbport):
	from utilities import getArtistInfo
	from htmlgenerators import clean, artistLink, artistLinks, trackLink, scrobblesTrackLink, getRangeDesc, scrobblesLink
	from htmlmodules import module_pulse, module_trackcharts

	allowedkeys = {"artist":keys.get("artist")}
#	clean(keys)
	info = getArtistInfo(keys["artist"])
	imgurl = info.get("image")
	#desc = info.get("info")
	pushresources = [{"file":imgurl,"type":"image"}] if imgurl.startswith("/") else []
	
	response = urllib.request.urlopen("http://[::1]:" + str(dbport) + "/artistinfo?artist=" + urllib.parse.quote(keys["artist"]))
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
		includestr += artistLinks(included)
	

	html_tracks, _ = module_trackcharts(**allowedkeys)	
	
	
	html_pulse = module_pulse(**allowedkeys,step="year",stepn=1,trail=1)

	replace = {"KEY_ARTISTNAME":keys["artist"],"KEY_ENC_ARTISTNAME":urllib.parse.quote(keys["artist"]),"KEY_IMAGEURL":imgurl, "KEY_DESCRIPTION":"","KEY_TRACKLIST":html_tracks,"KEY_SCROBBLES":scrobbles,"KEY_POSITION":pos,"KEY_ASSOCIATED":includestr,"KEY_PULSE":html_pulse}
	
	return (replace,pushresources)
