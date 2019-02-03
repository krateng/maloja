import urllib
import json

		
def replacedict(keys,dbport):
	from utilities import getArtistInfo, getArtistsInfo, getTracksInfo
	from htmlgenerators import artistLink, artistLinks, trackLink, scrobblesArtistLink, keysToUrl, pickKeys, clean, getTimeDesc
	
	max_show = 15
	posrange = ["#" + str(i) for i in range(1,max_show)]
	
	#clean(keys)
	#timekeys = pickKeys(keys,"since","to","in")
	#limitkeys = pickKeys(keys)
	
	# get chart data
	
	# artists
	response = urllib.request.urlopen("http://localhost:" + str(dbport) + "/charts/artists")
	db_data = json.loads(response.read())
	charts = db_data["list"][:max_show]
	topartist = charts[0]["artist"]
	
	artisttitles = [c["artist"] for c in charts]
	artistimages = [info.get("image") for info in getArtistsInfo(artisttitles)]
	artistlinks = [artistLink(a) for a in artisttitles]
	
	
	# tracks
	response = urllib.request.urlopen("http://localhost:" + str(dbport) + "/charts/tracks")
	db_data = json.loads(response.read())
	charts = db_data["list"][:max_show]
	
	trackobjects = [t["track"] for t in charts]
	tracktitles = [t["title"] for t in trackobjects]
	trackartists = [", ".join(t["artists"]) for t in trackobjects]
	trackimages = [info.get("image") for info in getTracksInfo(trackobjects)]
	tracklinks = [trackLink(t) for t in trackobjects]
	
	
	# get scrobbles
	response = urllib.request.urlopen("http://localhost:" + str(dbport) + "/scrobbles?max=50")
	db_data = json.loads(response.read())
	scrobblelist = db_data["list"]
	scrobbletrackobjects = scrobblelist #ignore the extra time attribute, the format should still work
	scrobbleartists = [", ".join([artistLink(a) for a in s["artists"]]) for s in scrobblelist]
	scrobbletitles = [s["title"] for s in scrobblelist]
	scrobbletimes = [getTimeDesc(s["time"],short=True) for s in scrobblelist]
	scrobbleimages = [info.get("image") for info in getTracksInfo(scrobbletrackobjects)]
	scrobbletracklinks = [trackLink(t) for t in scrobbletrackobjects]
	
	
	# get stats
	response = urllib.request.urlopen("http://localhost:" +str(dbport) + "/numscrobbles?since=today")
	stats = json.loads(response.read())
	scrobbles_today = "<a href='/scrobbles?since=today'>" + str(stats["amount"]) + "</a>"
	
	response = urllib.request.urlopen("http://localhost:" +str(dbport) + "/numscrobbles?since=month")
	stats = json.loads(response.read())
	scrobbles_month = "<a href='/scrobbles?since=month'>" + str(stats["amount"]) + "</a>"
	
	response = urllib.request.urlopen("http://localhost:" +str(dbport) + "/numscrobbles?since=year")
	stats = json.loads(response.read())
	scrobbles_year = "<a href='/scrobbles?since=year'>" + str(stats["amount"]) + "</a>"
	
	response = urllib.request.urlopen("http://localhost:" +str(dbport) + "/numscrobbles")
	stats = json.loads(response.read())
	scrobbles_total = "<a href='/scrobbles'>" + str(stats["amount"]) + "</a>"
	


	return {"KEY_ARTISTIMAGE":artistimages,"KEY_ARTISTNAME":artisttitles,"KEY_ARTISTLINK":artistlinks,"KEY_POSITION_ARTIST":posrange,
	"KEY_TRACKIMAGE":trackimages,"KEY_TRACKNAME":tracktitles,"KEY_TRACKLINK":tracklinks,"KEY_POSITION_TRACK":posrange,
	"KEY_SCROBBLES_TODAY":scrobbles_today,"KEY_SCROBBLES_MONTH":scrobbles_month,"KEY_SCROBBLES_YEAR":scrobbles_year,"KEY_SCROBBLES_TOTAL":scrobbles_total,
	"KEY_SCROBBLE_TIME":scrobbletimes,"KEY_SCROBBLE_ARTISTS":scrobbleartists,"KEY_SCROBBLE_TITLE":scrobbletracklinks,"KEY_SCROBBLE_IMAGE":scrobbleimages}

