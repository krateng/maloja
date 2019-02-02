import urllib
import json

		
def replacedict(keys,dbport):
	from utilities import getArtistInfo, getArtistsInfo
	from htmlgenerators import artistLink, artistLinks, trackLink, scrobblesArtistLink, keysToUrl, pickKeys, clean
	
	clean(keys)
	timekeys = pickKeys(keys,"since","to","in")
	limitkeys = pickKeys(keys)
	
	# get chart data
	response = urllib.request.urlopen("http://localhost:" + str(dbport) + "/charts/artists?" + keysToUrl(timekeys,limitkeys))
	db_data = json.loads(response.read())
	charts = db_data["list"][:50]
	topartist = charts[0]["artist"]
	
	chartslist = [c["artist"] for c in charts]
	#chartslistimg = [getArtistInfo(a).get("image") for a in chartslist]
	chartslistimg = [info.get("image") for info in getArtistsInfo(chartslist)]
	chartslistlink = [artistLink(a) for a in chartslist]
	
	
	# get total amount of scrobbles
	response = urllib.request.urlopen("http://localhost:" + str(dbport) + "/scrobbles?" + keysToUrl(timekeys,limitkeys))
	db_data = json.loads(response.read())
	scrobblelist = db_data["list"]
	scrobbles = len(scrobblelist)
	


	return {"KEY_ARTISTIMAGE":chartslistimg,"KEY_ARTISTNAME":chartslist,"KEY_ARTISTLINK":chartslistlink,"KEY_POSITION":["#" + str(i) for i in range(1,50)]}

