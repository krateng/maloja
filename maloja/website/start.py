import urllib
from datetime import datetime, timedelta
from .. import database
from doreah.timing import clock, clockp
from doreah.settings import get_settings

from ..htmlmodules import module_scrobblelist, module_pulse, module_artistcharts_tiles, module_trackcharts_tiles


def instructions(keys):

	# commands to execute on load for default ranges
	js_command = "showRange('topartists','" + get_settings("DEFAULT_RANGE_CHARTS_ARTISTS") + "');"
	js_command += "showRange('toptracks','" + get_settings("DEFAULT_RANGE_CHARTS_TRACKS") + "');"
	js_command += "showRange('pulse','" + get_settings("DEFAULT_STEP_PULSE") + "');"


	#clock()

	from ..malojatime import today,thisweek,thismonth,thisyear

	# artists

	topartists_total = module_artistcharts_tiles()
	topartists_year = module_artistcharts_tiles(timerange=thisyear())
	topartists_month = module_artistcharts_tiles(timerange=thismonth())
	topartists_week = module_artistcharts_tiles(timerange=thisweek())

	#clockp("Artists")

	# tracks

	toptracks_total = module_trackcharts_tiles()
	toptracks_year = module_trackcharts_tiles(timerange=thisyear())
	toptracks_month = module_trackcharts_tiles(timerange=thismonth())
	toptracks_week = module_trackcharts_tiles(timerange=thisweek())


	#clockp("Tracks")




	# scrobbles
	html_scrobbles, _, _ = module_scrobblelist(max_=15,shortTimeDesc=True,pictures=True,earlystop=True)

	#clockp("Scrobbles")

	# stats

	amount_day = database.get_scrobbles_num(timerange=today())
	scrobbles_today = "<a href='/scrobbles?in=today'>" + str(amount_day) + "</a>"

	amount_week = database.get_scrobbles_num(timerange=thisweek())
	scrobbles_week = "<a href='/scrobbles?in=week'>" + str(amount_week) + "</a>"

	amount_month = database.get_scrobbles_num(timerange=thismonth())
	scrobbles_month = "<a href='/scrobbles?in=month'>" + str(amount_month) + "</a>"

	amount_year = database.get_scrobbles_num(timerange=thisyear())
	scrobbles_year = "<a href='/scrobbles?in=year'>" + str(amount_year) + "</a>"

	amount_total = database.get_scrobbles_num()
	scrobbles_total = "<a href='/scrobbles'>" + str(amount_total) + "</a>"

	#clockp("Amounts")

	# pulse


	html_pulse_days = module_pulse(max_=7,since=today().next(-6),step="day",trail=1)
	html_pulse_weeks = module_pulse(max_=12,since=thisweek().next(-11),step="week",trail=1)
	html_pulse_months = module_pulse(max_=12,since=thismonth().next(-11),step="month",trail=1)
	html_pulse_years = module_pulse(max_=10,since=thisyear().next(-9),step="year",trail=1)


	#html_pulse_week = module_pulse(max_=7,since=weekstart,step="day",trail=1)
	#html_pulse_month = module_pulse(max_=30,since=[dt.year,dt.month],step="day",trail=1)
	#html_pulse_year = module_pulse(max_=12,since=[dt.year],step="month",trail=1)

	#clockp("Pulse")

	#pushresources = [{"file":img,"type":"image"} for img in artistimages + trackimages] #can't push scrobble images as we don't get them from the module function, need to think about that
	pushresources = []

	replace = {
	"KEY_TOPARTISTS_TOTAL":topartists_total,"KEY_TOPARTISTS_YEAR":topartists_year,"KEY_TOPARTISTS_MONTH":topartists_month,"KEY_TOPARTISTS_WEEK":topartists_week,
	"KEY_TOPTRACKS_TOTAL":toptracks_total,"KEY_TOPTRACKS_YEAR":toptracks_year,"KEY_TOPTRACKS_MONTH":toptracks_month,"KEY_TOPTRACKS_WEEK":toptracks_week,
	"KEY_JS_INIT_RANGES":js_command,
	"KEY_SCROBBLE_NUM_TODAY":scrobbles_today,"KEY_SCROBBLE_NUM_WEEK":scrobbles_week,"KEY_SCROBBLE_NUM_MONTH":scrobbles_month,"KEY_SCROBBLE_NUM_YEAR":scrobbles_year,"KEY_SCROBBLE_NUM_TOTAL":scrobbles_total,
	"KEY_SCROBBLES":html_scrobbles,
	"KEY_PULSE_MONTHS":html_pulse_months,"KEY_PULSE_YEARS":html_pulse_years,"KEY_PULSE_DAYS":html_pulse_days,"KEY_PULSE_WEEKS":html_pulse_weeks,
	#"KEY_PULSE_YEAR":html_pulse_year,"KEY_PULSE_MONTH":html_pulse_month,"KEY_PULSE_WEEK":html_pulse_week
	}

	return (replace,pushresources)
