import urllib
import json
from threading import Thread
from datetime import datetime
#import database

from htmlmodules import module_scrobblelist, module_pulse


def getpictures(ls,result,tracks=False):
	from utilities import getArtistsInfo, getTracksInfo
	if tracks:
		for element in getTracksInfo(ls):
			result.append(element.get("image"))
	else:
		for element in getArtistsInfo(ls):
			result.append(element.get("image"))
		
def instructions(keys,dbport):
	from utilities import getArtistsInfo, getTracksInfo
	from htmlgenerators import artistLink, artistLinks, trackLink, scrobblesArtistLink, scrobblesLink, keysToUrl, pickKeys, clean, getTimeDesc, getRangeDesc
	
	max_show = 15
	posrange = ["#" + str(i) for i in range(1,max_show)]
	
	
	#clean(keys)
	#timekeys = pickKeys(keys,"since","to","in")
	#limitkeys = pickKeys(keys)
	
	# get chart data
	
	# artists
	response = urllib.request.urlopen("http://[::1]:" + str(dbport) + "/charts/artists")
	db_data = json.loads(response.read())
	charts = db_data["list"][:max_show]
	#charts = database.get_charts_artists()[:max_show]
	topartist = charts[0]["artist"]
	
	artisttitles = [c["artist"] for c in charts]
	artistimages = []
	t1 = Thread(target=getpictures,args=(artisttitles,artistimages,))
	t1.start()
	#artistimages = [info.get("image") for info in getArtistsInfo(artisttitles)]
	artistlinks = [artistLink(a) for a in artisttitles]
	
	
	# tracks
	response = urllib.request.urlopen("http://[::1]:" + str(dbport) + "/charts/tracks")
	db_data = json.loads(response.read())
	charts = db_data["list"][:max_show]
	#charts = database.get_charts_trackss()[:max_show]
	
	trackobjects = [t["track"] for t in charts]
	tracktitles = [t["title"] for t in trackobjects]
	trackartists = [", ".join(t["artists"]) for t in trackobjects]
	trackimages = []
	t2 = Thread(target=getpictures,args=(trackobjects,trackimages,),kwargs={"tracks":True})
	t2.start()
	#trackimages = [info.get("image") for info in getTracksInfo(trackobjects)]
	tracklinks = [trackLink(t) for t in trackobjects]
	
	
	# get scrobbles
#	response = urllib.request.urlopen("http://[::1]:" + str(dbport) + "/scrobbles?max=50")
#	db_data = json.loads(response.read())
#	scrobblelist = db_data["list"]
#	#scrobblelist = database.get_scrobbles(max=50)
#	scrobbletrackobjects = scrobblelist #ignore the extra time attribute, the format should still work
#	scrobbleartists = [", ".join([artistLink(a) for a in s["artists"]]) for s in scrobblelist]
#	scrobbletitles = [s["title"] for s in scrobblelist]
#	scrobbletimes = [getTimeDesc(s["time"],short=True) for s in scrobblelist]
#	scrobbleimages = []
#	t3 = Thread(target=getpictures,args=(scrobbletrackobjects,scrobbleimages,),kwargs={"tracks":True})
#	t3.start()
#	#scrobbleimages = [info.get("image") for info in getTracksInfo(scrobbletrackobjects)]
#	scrobbletracklinks = [trackLink(t) for t in scrobbletrackobjects]
	
	html_scrobbles, _, _ = module_scrobblelist(max_=15,shortTimeDesc=True,pictures=True)
	
	
	# get stats
	response = urllib.request.urlopen("http://[::1]:" +str(dbport) + "/numscrobbles?since=today")
	stats = json.loads(response.read())
	scrobbles_today = "<a href='/scrobbles?since=today'>" + str(stats["amount"]) + "</a>"
	
	response = urllib.request.urlopen("http://[::1]:" +str(dbport) + "/numscrobbles?since=month")
	stats = json.loads(response.read())
	scrobbles_month = "<a href='/scrobbles?since=month'>" + str(stats["amount"]) + "</a>"
	
	response = urllib.request.urlopen("http://[::1]:" +str(dbport) + "/numscrobbles?since=year")
	stats = json.loads(response.read())
	scrobbles_year = "<a href='/scrobbles?since=year'>" + str(stats["amount"]) + "</a>"
	
	response = urllib.request.urlopen("http://[::1]:" +str(dbport) + "/numscrobbles")
	stats = json.loads(response.read())
	scrobbles_total = "<a href='/scrobbles'>" + str(stats["amount"]) + "</a>"
	
	
	# get pulse
	dt = datetime.utcnow()
	dtl = [dt.year-1,dt.month+1]
	if dtl[1] > 12: dtl = [dtl[0]+1,dtl[1]-12]
	dts = "/".join([str(e) for e in dtl])
	# this is literally the ugliest piece of code i have written in my entire feckin life
	# good lord
	
#	response = urllib.request.urlopen("http://[::1]:" + str(dbport) + "/pulse?step=month&trail=1&since=" + dts)
#	db_data = json.loads(response.read())
#	terms = db_data["list"]

#	maxbar = max([t["scrobbles"] for t in terms])
#	#pulse_fromdates = ["/".join([str(e) for e in t["from"]]) for t in terms]
#	#pulse_todates = ["/".join([str(e) for e in t["to"]]) for t in terms]
#	pulse_rangedescs = [getRangeDesc(t["from"],t["to"]) for t in terms]
#	pulse_amounts = [scrobblesLink({"since":"/".join([str(e) for e in t["from"]]),"to":"/".join([str(e) for e in t["to"]])},amount=t["scrobbles"]) for t in terms]
#	pulse_bars = [scrobblesLink({"since":"/".join([str(e) for e in t["from"]]),"to":"/".join([str(e) for e in t["to"]])},percent=t["scrobbles"]*100/maxbar) for t in terms]
	
	html_pulse = module_pulse(max_=12,since=dts,step="month",trail=1)	
	
	
	
	t1.join()
	t2.join()
	#t3.join()
	
	#pushresources = [{"file":img,"type":"image"} for img in artistimages + trackimages + scrobbleimages if img.startswith("/")]
	pushresources = []

	replace = {"KEY_ARTISTIMAGE":artistimages,"KEY_ARTISTNAME":artisttitles,"KEY_ARTISTLINK":artistlinks,"KEY_POSITION_ARTIST":posrange,
	"KEY_TRACKIMAGE":trackimages,"KEY_TRACKNAME":tracktitles,"KEY_TRACKLINK":tracklinks,"KEY_POSITION_TRACK":posrange,
	"KEY_SCROBBLES_TODAY":scrobbles_today,"KEY_SCROBBLES_MONTH":scrobbles_month,"KEY_SCROBBLES_YEAR":scrobbles_year,"KEY_SCROBBLES_TOTAL":scrobbles_total,
	#"KEY_SCROBBLE_TIME":scrobbletimes,"KEY_SCROBBLE_ARTISTS":scrobbleartists,"KEY_SCROBBLE_TITLE":scrobbletracklinks,"KEY_SCROBBLE_IMAGE":scrobbleimages,
	"KEY_SCROBBLES":html_scrobbles,
	#"KEY_PULSE_TERM":pulse_rangedescs,"KEY_PULSE_AMOUNT":pulse_amounts,"KEY_PULSE_BAR":pulse_bars
	"KEY_PULSE":html_pulse
	}
	
	return (replace,pushresources)

