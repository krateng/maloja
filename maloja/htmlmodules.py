from .htmlgenerators import *
from . import database
from .utilities import getArtistImage, getTrackImage
from .malojatime import *
from .urihandler import compose_querystring, internal_to_uri, uri_to_internal
import urllib
import datetime
import math


#def getpictures(ls,result,tracks=False):
#	from utilities import getArtistsInfo, getTracksInfo
#	if tracks:
#		for element in getTracksInfo(ls):
#			result.append(element.get("image"))
#	else:
#		for element in getArtistsInfo(ls):
#			result.append(element.get("image"))


#max_ indicates that no pagination should occur (because this is not the primary module)
def module_scrobblelist(page=0,perpage=100,max_=None,pictures=False,shortTimeDesc=False,earlystop=False,**kwargs):

	kwargs_filter = pickKeys(kwargs,"artist","track","associated")
	kwargs_time = pickKeys(kwargs,"timerange","since","to","within")

	if max_ is not None: perpage,page=max_,0

	firstindex = page * perpage
	lastindex = firstindex + perpage

	# if earlystop, we don't care about the actual amount and only request as many from the db
	# without, we request everything and filter on site
	maxkey = {"max_":lastindex} if earlystop else {}
	scrobbles = database.get_scrobbles(**kwargs_time,**kwargs_filter,**maxkey)
	if pictures:
		scrobbleswithpictures = [""] * firstindex + scrobbles[firstindex:lastindex]
		#scrobbleimages = [e.get("image") for e in getTracksInfo(scrobbleswithpictures)] #will still work with scrobble objects as they are a technically a subset of track objects
		#scrobbleimages = ["/image?title=" + urllib.parse.quote(t["title"]) + "&" + "&".join(["artist=" + urllib.parse.quote(a) for a in t["artists"]])  for t in scrobbleswithpictures]
		scrobbleimages = [getTrackImage(t["artists"],t["title"],fast=True) for t in scrobbleswithpictures]

	pages = math.ceil(len(scrobbles) / perpage)

	representative = scrobbles[0] if len(scrobbles) is not 0 else None

	# build list
	i = 0
	html = "<table class='list'>"
	for s in scrobbles:
		if i<firstindex:
			i += 1
			continue

		html += "<tr>"
		html += "<td class='time'>" + timestamp_desc(s["time"],short=shortTimeDesc) + "</td>"
		if pictures:
			img = scrobbleimages[i]
		else: img = None
		html += entity_column(s,image=img)
		html += "</tr>"

		i += 1
		if i>=lastindex:
			break


	html += "</table>"

	if max_ is None: html += module_paginate(page=page,pages=pages,perpage=perpage,**kwargs)

	return (html,len(scrobbles),representative)


def module_pulse(page=0,perpage=100,max_=None,**kwargs):

	from doreah.timing import clock, clockp

	kwargs_filter = pickKeys(kwargs,"artist","track","associated")
	kwargs_time = pickKeys(kwargs,"since","to","within","timerange","step","stepn","trail")

	if max_ is not None: perpage,page=max_,0

	firstindex = page * perpage
	lastindex = firstindex + perpage


	ranges = database.get_pulse(**kwargs_time,**kwargs_filter)

	pages = math.ceil(len(ranges) / perpage)

	ranges = ranges[firstindex:lastindex]

	# if time range not explicitly specified, only show from first appearance
#	if "since" not in kwargs:
#		while ranges[0]["scrobbles"] == 0:
#			del ranges[0]

	maxbar = max([t["scrobbles"] for t in ranges])
	maxbar = max(maxbar,1)

	#build list
	html = "<table class='list'>"
	for t in ranges:
		range = t["range"]
		html += "<tr>"
		html += "<td>" + range.desc() + "</td>"
		html += "<td class='amount'>" + scrobblesLink(range.urikeys(),amount=t["scrobbles"],**kwargs_filter) + "</td>"
		html += "<td class='bar'>" + scrobblesLink(range.urikeys(),percent=t["scrobbles"]*100/maxbar,**kwargs_filter) + "</td>"
		html += "</tr>"
	html += "</table>"

	if max_ is None: html += module_paginate(page=page,pages=pages,perpage=perpage,**kwargs)

	return html



def module_performance(page=0,perpage=100,max_=None,**kwargs):

	kwargs_filter = pickKeys(kwargs,"artist","track")
	kwargs_time = pickKeys(kwargs,"since","to","within","timerange","step","stepn","trail")

	if max_ is not None: perpage,page=max_,0

	firstindex = page * perpage
	lastindex = firstindex + perpage

	ranges = database.get_performance(**kwargs_time,**kwargs_filter)

	pages = math.ceil(len(ranges) / perpage)

	ranges = ranges[firstindex:lastindex]

	# if time range not explicitly specified, only show from first appearance
#	if "since" not in kwargs:
#		while ranges[0]["scrobbles"] == 0:
#			del ranges[0]


	minrank = 80
	for t in ranges:
		if t["rank"] is not None and t["rank"]+20 > minrank: minrank = t["rank"]+20

	#build list
	html = "<table class='list'>"
	for t in ranges:
		range = t["range"]
		html += "<tr>"
		html += "<td>" + range.desc() + "</td>"
		html += "<td class='rank'>" + ("#" + str(t["rank"]) if t["rank"] is not None else "No scrobbles") + "</td>"
		prct = (minrank+1-t["rank"])*100/minrank if t["rank"] is not None else 0
		html += "<td class='chart'>" + rankLink(range.urikeys(),percent=prct,**kwargs_filter,medal=t["rank"]) + "</td>"
		html += "</tr>"
	html += "</table>"

	if max_ is None: html += module_paginate(page=page,pages=pages,perpage=perpage,**kwargs)

	return html



def module_trackcharts(page=0,perpage=100,max_=None,**kwargs):

	kwargs_filter = pickKeys(kwargs,"artist","associated")
	kwargs_time = pickKeys(kwargs,"timerange","since","to","within")

	if max_ is not None: perpage,page=max_,0

	firstindex = page * perpage
	lastindex = firstindex + perpage

	tracks = database.get_charts_tracks(**kwargs_filter,**kwargs_time)

	pages = math.ceil(len(tracks) / perpage)

	# last time range (to compare)
	try:
		trackslast = database.get_charts_tracks(**kwargs_filter,timerange=kwargs_time["timerange"].next(step=-1))
		# create rank association
		lastrank = {}
		for tl in trackslast:
			lastrank[(*tl["track"]["artists"],tl["track"]["title"])] = tl["rank"]
		for t in tracks:
			try:
				t["delta"] = lastrank[(*t["track"]["artists"],t["track"]["title"])] - t["rank"]
			except:
				t["delta"] = math.inf
	except:
		pass

	if tracks != []:
		maxbar = tracks[0]["scrobbles"]
		representative = tracks[0]["track"]
	else:
		representative = None


	i = 0
	html = "<table class='list'>"
	for e in tracks:
		if i<firstindex:
			i += 1
			continue
		i += 1
		if i>lastindex:
			break
		html += "<tr>"
		# rank
		if i == firstindex+1 or e["scrobbles"] < prev["scrobbles"]:
			html += "<td class='rank'>#" + str(e["rank"]) + "</td>"
		else:
			html += "<td class='rank'></td>"
		# rank change
		if e.get("delta") is None:
			pass
		elif e["delta"] is math.inf:
			html += "<td class='rankup' title='New'>🆕</td>"
		elif e["delta"] > 0:
			html += "<td class='rankup' title='up from #" + str(e["rank"]+e["delta"]) + "'>↗</td>"
		elif e["delta"] < 0:
			html += "<td class='rankdown' title='down from #" + str(e["rank"]+e["delta"]) + "'>↘</td>"
		else:
			html += "<td class='ranksame' title='Unchanged'>➡</td>"
		# track
		html += entity_column(e["track"])
		# scrobbles
		html += "<td class='amount'>" + scrobblesTrackLink(e["track"],internal_to_uri(kwargs_time),amount=e["scrobbles"]) + "</td>"
		html += "<td class='bar'>" + scrobblesTrackLink(e["track"],internal_to_uri(kwargs_time),percent=e["scrobbles"]*100/maxbar) + "</td>"
		html += "</tr>"
		prev = e
	html += "</table>"

	if max_ is None: html += module_paginate(page=page,pages=pages,perpage=perpage,**kwargs)

	return (html,representative)


def module_artistcharts(page=0,perpage=100,max_=None,**kwargs):

	kwargs_filter = pickKeys(kwargs,"associated") #not used right now
	kwargs_time = pickKeys(kwargs,"timerange","since","to","within")

	if max_ is not None: perpage,page=max_,0

	firstindex = page * perpage
	lastindex = firstindex + perpage

	artists = database.get_charts_artists(**kwargs_filter,**kwargs_time)

	pages = math.ceil(len(artists) / perpage)


	# last time range (to compare)
	try:
	#from malojatime import _get_next
		artistslast = database.get_charts_artists(**kwargs_filter,timerange=kwargs_time["timerange"].next(step=-1))
		# create rank association
		lastrank = {}
		for al in artistslast:
			lastrank[al["artist"]] = al["rank"]
		for a in artists:
			try:
				a["delta"] = lastrank[a["artist"]] - a["rank"]
			except:
				a["delta"] = math.inf
	except:
		pass

	if artists != []:
		maxbar = artists[0]["scrobbles"]
		representative = artists[0]["artist"]
	else:
		representative = None

	i = 0
	html = "<table class='list'>"
	for e in artists:
		if i<firstindex:
			i += 1
			continue
		i += 1
		if i>lastindex:
			break
		html += "<tr>"
		# rank
		if i == firstindex+1 or e["scrobbles"] < prev["scrobbles"]:
			html += "<td class='rank'>#" + str(e["rank"]) + "</td>"
		else:
			html += "<td class='rank'></td>"
		# rank change
		#if "within" not in kwargs_time: pass
		if e.get("delta") is None:
			pass
		elif e["delta"] is math.inf:
			html += "<td class='rankup' title='New'>🆕</td>"
		elif e["delta"] > 0:
			html += "<td class='rankup' title='up from #" + str(e["rank"]+e["delta"]) + "'>↗</td>"
		elif e["delta"] < 0:
			html += "<td class='rankdown' title='down from #" + str(e["rank"]+e["delta"]) + "'>↘</td>"
		else:
			html += "<td class='ranksame' title='Unchanged'>➡</td>"
		# artist
		html += entity_column(e["artist"],counting=e["counting"])
		# scrobbles
		html += "<td class='amount'>" + scrobblesArtistLink(e["artist"],internal_to_uri(kwargs_time),amount=e["scrobbles"],associated=True) + "</td>"
		html += "<td class='bar'>" + scrobblesArtistLink(e["artist"],internal_to_uri(kwargs_time),percent=e["scrobbles"]*100/maxbar,associated=True) + "</td>"
		html += "</tr>"
		prev = e

	html += "</table>"

	if max_ is None: html += module_paginate(page=page,pages=pages,perpage=perpage,**kwargs)

	return (html, representative)



def module_toptracks(pictures=True,**kwargs):

	kwargs_filter = pickKeys(kwargs,"artist","associated")
	kwargs_time = pickKeys(kwargs,"timerange","since","to","within","step","stepn","trail")

	tracks = database.get_top_tracks(**kwargs_filter,**kwargs_time)

	if tracks != []:
		maxbar = max(t["scrobbles"] for t in tracks)


		# track with most #1 positions
		max_appear = 0
		representatives = list(t["track"] for t in tracks if t["track"] is not None)
		for t in representatives:
			max_appear = max(max_appear,representatives.count(t))
		#representatives.sort(key=lambda reftrack:len([t for t in tracks if t["track"] == reftrack["track"] and t["track"] is not None]))
		representatives = [t for t in tracks if representatives.count(t["track"]) == max_appear]
		# of these, track with highest scrobbles in its #1 range
		representatives.sort(key=lambda t: t["scrobbles"])
		representative = representatives[-1]["track"]
	else:
		representative = None


	i = 0
	html = "<table class='list'>"
	for e in tracks:

		#fromstr = "/".join([str(p) for p in e["from"]])
		#tostr = "/".join([str(p) for p in e["to"]])
		range = e["range"]

		i += 1
		html += "<tr>"


		html += "<td>" + range.desc() + "</td>"
		if e["track"] is None:
			if pictures:
				html += "<td><div></div></td>"
			html += "<td class='stats'>" + "No scrobbles" + "</td>"
			#html += "<td>" + "" + "</td>"
			html += "<td class='amount'>" + "0" + "</td>"
			html += "<td class='bar'>" + "" + "</td>"
		else:
			if pictures:
				img = getTrackImage(e["track"]["artists"],e["track"]["title"],fast=True)
			else: img = None
			html += entity_column(e["track"],image=img)
			html += "<td class='amount'>" + scrobblesTrackLink(e["track"],range.urikeys(),amount=e["scrobbles"]) + "</td>"
			html += "<td class='bar'>" + scrobblesTrackLink(e["track"],range.urikeys(),percent=e["scrobbles"]*100/maxbar) + "</td>"
		html += "</tr>"
		prev = e
	html += "</table>"

	return (html,representative)

def module_topartists(pictures=True,**kwargs):

	kwargs_time = pickKeys(kwargs,"timerange","since","to","within","step","stepn","trail")

	artists = database.get_top_artists(**kwargs_time)

	if artists != []:
		maxbar = max(a["scrobbles"] for a in artists)

		# artists with most #1 positions
		max_appear = 0
		representatives = list(a["artist"] for a in artists if a["artist"] is not None)
		for a in representatives:
			max_appear = max(max_appear,representatives.count(a))
		representatives = [a for a in artists if representatives.count(a["artist"]) == max_appear]
		# of these, artist with highest scrobbles in their #1 range
		representatives.sort(key=lambda a: a["scrobbles"])

		representative = representatives[-1]["artist"]
	else:
		representative = None


	i = 0
	html = "<table class='list'>"
	for e in artists:

		#fromstr = "/".join([str(p) for p in e["from"]])
		#tostr = "/".join([str(p) for p in e["to"]])
		range = e["range"]

		i += 1
		html += "<tr>"


		html += "<td>" + range.desc() + "</td>"

		if e["artist"] is None:
			if pictures:
				html += "<td><div></div></td>"
			html += "<td class='stats'>" + "No scrobbles" + "</td>"
			html += "<td class='amount'>" + "0" + "</td>"
			html += "<td class='bar'>" + "" + "</td>"
		else:
			if pictures:
				img = getArtistImage(e["artist"],fast=True)
			else: img = None
			html += entity_column(e["artist"],image=img)
			html += "<td class='amount'>" + scrobblesArtistLink(e["artist"],range.urikeys(),amount=e["scrobbles"],associated=True) + "</td>"
			html += "<td class='bar'>" + scrobblesArtistLink(e["artist"],range.urikeys(),percent=e["scrobbles"]*100/maxbar,associated=True) + "</td>"
		html += "</tr>"
		prev = e
	html += "</table>"

	return (html,representative)


def module_artistcharts_tiles(**kwargs):

	kwargs_filter = pickKeys(kwargs,"associated") #not used right now
	kwargs_time = pickKeys(kwargs,"timerange","since","to","within")

	artists = database.get_charts_artists(**kwargs_filter,**kwargs_time)[:14]
	while len(artists)<14: artists.append(None)

	i = 1

	bigpart = [0,1,2,6,15]
	smallpart = [0,1,2,4,6,9,12,15]
	#rnk = (0,0) #temporary store so entries with the same scrobble amount get the same rank

	html = """<table class="tiles_top"><tr>"""

	for e in artists:


		if i in bigpart:
			n = bigpart.index(i)
			html += """<td><table class="tiles_""" + str(n) + """x""" + str(n) + """ tiles_sub">"""

		if i in smallpart:
			html += "<tr>"


		if e is not None:
			html += "<td onclick='window.location.href=\"" \
				+ link_address(e["artist"]) \
				+ "\"' style='cursor:pointer;background-image:url(\"" + getArtistImage(e["artist"],fast=True) + "\");'>" \
				+ "<span class='stats'>" + "#" + str(e["rank"]) + "</span> <span>" + html_link(e["artist"]) + "</span></td>"
		else:
			html += "<td><span class='stats'></span> <span></span></td>"

		i += 1

		if i in smallpart:
			html += "</tr>"

		if i in bigpart:
			html += "</table></td>"

	html += """</tr></table>"""

	return html


def module_trackcharts_tiles(**kwargs):

	kwargs_filter = pickKeys(kwargs,"artist","associated")
	kwargs_time = pickKeys(kwargs,"timerange","since","to","within")

	tracks = database.get_charts_tracks(**kwargs_filter,**kwargs_time)[:14]
	while len(tracks)<14: tracks.append(None) #{"track":{"title":"","artists":[]}}

	i = 1

	bigpart = [0,1,2,6,15]
	smallpart = [0,1,2,4,6,9,12,15]
	#rnk = (0,0) #temporary store so entries with the same scrobble amount get the same rank


	html = """<table class="tiles_top"><tr>"""

	for e in tracks:


		if i in bigpart:
			n = bigpart.index(i)
			html += """<td><table class="tiles_""" + str(n) + """x""" + str(n) + """ tiles_sub">"""

		if i in smallpart:
			html += "<tr>"


		if e is not None:
			html += "<td onclick='window.location.href=\"" \
				+ link_address(e["track"]) \
				+ "\"' style='cursor:pointer;background-image:url(\"" + getTrackImage(e["track"]["artists"],e["track"]["title"],fast=True) + "\");'>" \
				+ "<span class='stats'>" + "#" + str(e["rank"]) + "</span> <span>" + html_link(e["track"]) + "</span></td>"
		else:
			html += "<td><span class='stats'></span> <span></span></td>"

		i += 1

		if i in smallpart:
			html += "</tr>"

		if i in bigpart:
			html += "</table></td>"

	html += """</tr></table>"""

	return html



def module_paginate(page,pages,perpage,**keys):

	unchangedkeys = internal_to_uri({**keys,"perpage":perpage})

	html = "<div class='paginate'>"

	if page > 1:
		html += "<a href='?" + compose_querystring(unchangedkeys,internal_to_uri({"page":0})) + "'><span class='stat_selector'>" + "1" + "</span></a>"
		html += " | "

	if page > 2:
		html += " ... | "

	if page > 0:
		html += "<a href='?" + compose_querystring(unchangedkeys,internal_to_uri({"page":page-1})) + "'><span class='stat_selector'>" + str(page) + "</span></a>"
		html += " « "

	html += "<span style='opacity:0.5;' class='stat_selector'>" + str(page+1) + "</span>"

	if page < pages-1:
		html += " » "
		html += "<a href='?" + compose_querystring(unchangedkeys,internal_to_uri({"page":page+1})) + "'><span class='stat_selector'>" + str(page+2) + "</span></a>"

	if page < pages-3:
		html += " | ... "

	if page < pages-2:
		html += " | "
		html += "<a href='?" + compose_querystring(unchangedkeys,internal_to_uri({"page":pages-1})) + "'><span class='stat_selector'>" + str(pages) + "</span></a>"


	html += "</div>"

	return html



# THIS FUNCTION USES THE ORIGINAL URI KEYS!!!
def module_filterselection(keys,time=True,delimit=False):

	from .malojatime import today, thisweek, thismonth, thisyear, alltime

	filterkeys, timekeys, delimitkeys, extrakeys = uri_to_internal(keys)
	# drop keys that are not relevant so they don't clutter the URI
	if not time: timekeys = {}
	if not delimit: delimitkeys = {}
	if "page" in extrakeys: del extrakeys["page"]
	internalkeys = {**filterkeys,**timekeys,**delimitkeys,**extrakeys}

	html = ""


	if time:

		# wonky selector for precise date range

#		fromdate = start_of_scrobbling()
#		todate = end_of_scrobbling()
#		if keys.get("since") is not None: fromdate = keys.get("since")
#		if keys.get("to") is not None: todate = keys.get("to")
#		if keys.get("in") is not None: fromdate, todate = keys.get("in"), keys.get("in")
#		fromdate = time_fix(fromdate)
#		todate = time_fix(todate)
#		fromdate, todate = time_pad(fromdate,todate,full=True)
#		fromdate = [str(e) if e>9 else "0" + str(e) for e in fromdate]
#		todate = [str(e) if e>9 else "0" + str(e) for e in todate]
#
#		html += "<div>"
#		html += "from <input id='dateselect_from' onchange='datechange()' type='date' value='" + "-".join(fromdate) + "'/> "
#		html += "to <input id='dateselect_to' onchange='datechange()' type='date' value='" + "-".join(todate) + "'/>"
#		html += "</div>"

		# relative to current range
		html += "<div>"

		thisrange = timekeys.get("timerange")
		prevrange = thisrange.next(-1)
		nextrange = thisrange.next(1)

		if prevrange is not None:
			link = compose_querystring(internal_to_uri({**internalkeys,"timerange":prevrange}))
			html += "<a href='?" + link + "'><span class='stat_selector'>" + prevrange.desc() + "</span></a>"
			html += " « "
		if prevrange is not None or nextrange is not None:
			html += "<span class='stat_selector' style='opacity:0.5;'>" + thisrange.desc() + "</span>"
		if nextrange is not None:
			html += " » "
			link = compose_querystring(internal_to_uri({**internalkeys,"timerange":nextrange}))
			html += "<a href='?" + link + "'><span class='stat_selector'>" + nextrange.desc() + "</span></a>"

		html += "</div>"




	categories = [
		{
			"active":time,
			"options":{
				"Today":{"timerange":today()},
				"This Week":{"timerange":thisweek()},
				"This Month":{"timerange":thismonth()},
				"This Year":{"timerange":thisyear()},
				"All Time":{"timerange":alltime()}
			}
		},
		{
			"active":delimit,
			"options":{
				"Daily":{"step":"day","stepn":1},
				"Weekly":{"step":"week","stepn":1},
				"Fortnightly":{"step":"week","stepn":2},
				"Monthly":{"step":"month","stepn":1},
				"Quarterly":{"step":"month","stepn":3},
				"Yearly":{"step":"year","stepn":1}
			}
		},
		{
			"active":delimit,
			"options":{
				"Standard":{"trail":1},
				"Trailing":{"trail":2},
				"Long Trailing":{"trail":3},
				"Inert":{"trail":10},
				"Cumulative":{"trail":math.inf}
			}
		}

	]

	for c in categories:

		if c["active"]:

			optionlist = []
			for option in c["options"]:
				values = c["options"][option]
				link = "?" + compose_querystring(internal_to_uri({**internalkeys,**values}))

				if all(internalkeys.get(k) == values[k] for k in values):
					optionlist.append("<span class='stat_selector' style='opacity:0.5;'>" + option + "</span>")
				else:
					optionlist.append("<a href='" + link + "'><span class='stat_selector'>" + option + "</span></a>")

			html += "<div>" + " | ".join(optionlist) + "</div>"

	return html
