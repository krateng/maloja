import urllib
from datetime import datetime, timedelta
import database

from htmlmodules import module_scrobblelist, module_pulse, module_artistcharts_tiles, module_trackcharts_tiles

		
def instructions(keys):
	from utilities import getArtistsInfo, getTracksInfo
	from htmlgenerators import artistLink, trackLink
	
#	max_show = 14
#	posrange = ["#" + str(i) for i in range(1,max_show+1)]

	# get chart data
	
	# artists
#	charts = database.get_charts_artists()[:max_show]	
#	artisttitles = [c["artist"] for c in charts]
#	artistimages = ["/image?artist=" + urllib.parse.quote(a) for a in artisttitles]
#	artistlinks = [artistLink(a) for a in artisttitles]
	
	topartists_total = module_artistcharts_tiles()
	topartists_year = module_artistcharts_tiles(since="year")
	topartists_month = module_artistcharts_tiles(since="month")
	topartists_week = module_artistcharts_tiles(since="week")
	
	
	# tracks
#	charts = database.get_charts_tracks()[:max_show]
#	trackobjects = [t["track"] for t in charts]
#	tracktitles = [t["title"] for t in trackobjects]
#	trackimages = ["/image?title=" + urllib.parse.quote(t["title"]) + "&" + "&".join(["artist=" + urllib.parse.quote(a) for a in t["artists"]])  for t in trackobjects]
#	tracklinks = [trackLink(t) for t in trackobjects]
	
	toptracks_total = module_trackcharts_tiles()
	toptracks_year = module_trackcharts_tiles(since="year")
	toptracks_month = module_trackcharts_tiles(since="month")
	toptracks_week = module_trackcharts_tiles(since="week")
	
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
	first_month = [dt.year-1,dt.month+1]
	dt_firstweek = dt - timedelta(11*7) - timedelta((6-dt.weekday()))
	first_week = [dt_firstweek.year,dt_firstweek.month,dt_firstweek.day]
	dt_firstday = dt - timedelta(6)
	first_day = [dt_firstday.year,dt_firstday.month,dt_firstday.day]
	first_year = [dt.year - 9]
	
	if first_month[1] > 12: first_month = [first_month[0]+1,first_month[1]-12]
	#while first_week[2]
	
	
	#first_month = "/".join([str(e) for e in first_month])
	# this is literally the ugliest piece of code i have written in my entire feckin life
	# good lord
	
	html_pulse_days = module_pulse(max_=7,since=first_day,step="day",trail=1)
	html_pulse_weeks = module_pulse(max_=12,since=first_week,step="week",trail=1)
	html_pulse_months = module_pulse(max_=12,since=first_month,step="month",trail=1)	
	html_pulse_years = module_pulse(max_=10,since=first_year,step="year",trail=1)

	#pushresources = [{"file":img,"type":"image"} for img in artistimages + trackimages] #can't push scrobble images as we don't get them from the module function, need to think about that
	pushresources = []

	replace = {
#	"KEY_ARTISTIMAGE":artistimages,"KEY_ARTISTNAME":artisttitles,"KEY_ARTISTLINK":artistlinks,"KEY_POSITION_ARTIST":posrange,
#	"KEY_TRACKIMAGE":trackimages,"KEY_TRACKNAME":tracktitles,"KEY_TRACKLINK":tracklinks,"KEY_POSITION_TRACK":posrange,
	"KEY_TOPARTISTS_TOTAL":topartists_total,"KEY_TOPARTISTS_YEAR":topartists_year,"KEY_TOPARTISTS_MONTH":topartists_month,"KEY_TOPARTISTS_WEEK":topartists_week,
	"KEY_TOPTRACKS_TOTAL":toptracks_total,"KEY_TOPTRACKS_YEAR":toptracks_year,"KEY_TOPTRACKS_MONTH":toptracks_month,"KEY_TOPTRACKS_WEEK":toptracks_week,
	"KEY_SCROBBLES_TODAY":scrobbles_today,"KEY_SCROBBLES_MONTH":scrobbles_month,"KEY_SCROBBLES_YEAR":scrobbles_year,"KEY_SCROBBLES_TOTAL":scrobbles_total,
	#"KEY_SCROBBLE_TIME":scrobbletimes,"KEY_SCROBBLE_ARTISTS":scrobbleartists,"KEY_SCROBBLE_TITLE":scrobbletracklinks,"KEY_SCROBBLE_IMAGE":scrobbleimages,
	"KEY_SCROBBLES":html_scrobbles,
	#"KEY_PULSE_TERM":pulse_rangedescs,"KEY_PULSE_AMOUNT":pulse_amounts,"KEY_PULSE_BAR":pulse_bars
	"KEY_PULSE_MONTHS":html_pulse_months,"KEY_PULSE_YEARS":html_pulse_years,"KEY_PULSE_DAYS":html_pulse_days,"KEY_PULSE_WEEKS":html_pulse_weeks
	}
	
	return (replace,pushresources)

