import urllib
from datetime import datetime
import database

from htmlmodules import module_scrobblelist, module_pulse

		
def instructions(keys):
	from utilities import getArtistsInfo, getTracksInfo
	from htmlgenerators import artistLink, artistLinks, trackLink, scrobblesArtistLink, scrobblesLink, keysToUrl, pickKeys, clean, getTimeDesc, getRangeDesc
	
	max_show = 14
	posrange = ["#" + str(i) for i in range(1,max_show+1)]

	# get chart data
	
	# artists
	charts = database.get_charts_artists()[:max_show]	
	artisttitles = [c["artist"] for c in charts]
	artistimages = ["/image?artist=" + urllib.parse.quote(a) for a in artisttitles]
	artistlinks = [artistLink(a) for a in artisttitles]
	
	
	# tracks
	charts = database.get_charts_tracks()[:max_show]
	trackobjects = [t["track"] for t in charts]
	tracktitles = [t["title"] for t in trackobjects]
	trackimages = ["/image?title=" + urllib.parse.quote(t["title"]) + "&" + "&".join(["artist=" + urllib.parse.quote(a) for a in t["artists"]])  for t in trackobjects]
	tracklinks = [trackLink(t) for t in trackobjects]
	
	
	# get scrobbles
	html_scrobbles, _, _ = module_scrobblelist(max_=15,shortTimeDesc=True,pictures=True)
	
	
	# get stats
	amount = database.get_scrobbles_num(since="today")
	scrobbles_today = "<a href='/scrobbles?since=today'>" + str(amount) + "</a>"
	
	amount = database.get_scrobbles_num(since="month")
	scrobbles_month = "<a href='/scrobbles?since=month'>" + str(amount) + "</a>"

	amount = database.get_scrobbles_num(since="year")
	scrobbles_year = "<a href='/scrobbles?since=year'>" + str(amount) + "</a>"

	amount = database.get_scrobbles_num()
	scrobbles_total = "<a href='/scrobbles'>" + str(amount) + "</a>"
	
	
	# get pulse
	dt = datetime.utcnow()
	dtl = [dt.year-1,dt.month+1]
	if dtl[1] > 12: dtl = [dtl[0]+1,dtl[1]-12]
	dts = "/".join([str(e) for e in dtl])
	# this is literally the ugliest piece of code i have written in my entire feckin life
	# good lord
	
	html_pulse = module_pulse(max_=12,since=dts,step="month",trail=1)	


	pushresources = [{"file":img,"type":"image"} for img in artistimages + trackimages] #can't push scrobble images as we don't get them from the module function, need to think about that

	replace = {"KEY_ARTISTIMAGE":artistimages,"KEY_ARTISTNAME":artisttitles,"KEY_ARTISTLINK":artistlinks,"KEY_POSITION_ARTIST":posrange,
	"KEY_TRACKIMAGE":trackimages,"KEY_TRACKNAME":tracktitles,"KEY_TRACKLINK":tracklinks,"KEY_POSITION_TRACK":posrange,
	"KEY_SCROBBLES_TODAY":scrobbles_today,"KEY_SCROBBLES_MONTH":scrobbles_month,"KEY_SCROBBLES_YEAR":scrobbles_year,"KEY_SCROBBLES_TOTAL":scrobbles_total,
	#"KEY_SCROBBLE_TIME":scrobbletimes,"KEY_SCROBBLE_ARTISTS":scrobbleartists,"KEY_SCROBBLE_TITLE":scrobbletracklinks,"KEY_SCROBBLE_IMAGE":scrobbleimages,
	"KEY_SCROBBLES":html_scrobbles,
	#"KEY_PULSE_TERM":pulse_rangedescs,"KEY_PULSE_AMOUNT":pulse_amounts,"KEY_PULSE_BAR":pulse_bars
	"KEY_PULSE":html_pulse
	}
	
	return (replace,pushresources)

