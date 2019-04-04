from htmlgenerators import *
import database
from utilities import getArtistImage, getTrackImage
from malojatime import *
import urllib


#def getpictures(ls,result,tracks=False):
#	from utilities import getArtistsInfo, getTracksInfo
#	if tracks:
#		for element in getTracksInfo(ls):
#			result.append(element.get("image"))
#	else:
#		for element in getArtistsInfo(ls):
#			result.append(element.get("image"))


# artist=None,track=None,since=None,to=None,within=None,associated=False,max_=None,pictures=False
def module_scrobblelist(max_=None,pictures=False,shortTimeDesc=False,earlystop=False,**kwargs):

	kwargs_filter = pickKeys(kwargs,"artist","track","associated")
	kwargs_time = pickKeys(kwargs,"since","to","within")


	# if earlystop, we don't care about the actual amount and only request as many from the db
	# without, we request everything and filter on site
	maxkey = {"max_":max_} if earlystop else {}
	scrobbles = database.get_scrobbles(**kwargs_time,**kwargs_filter,**maxkey)
	if pictures:
		scrobbleswithpictures = scrobbles if max_ is None else scrobbles[:max_]
		#scrobbleimages = [e.get("image") for e in getTracksInfo(scrobbleswithpictures)] #will still work with scrobble objects as they are a technically a subset of track objects
		#scrobbleimages = ["/image?title=" + urllib.parse.quote(t["title"]) + "&" + "&".join(["artist=" + urllib.parse.quote(a) for a in t["artists"]])  for t in scrobbleswithpictures]
		scrobbleimages = [getTrackImage(t["artists"],t["title"],fast=True) for t in scrobbleswithpictures]

	representative = scrobbles[0] if len(scrobbles) is not 0 else None

	# build list
	i = 0
	html = "<table class='list'>"
	for s in scrobbles:

		html += "<tr>"
		html += "<td class='time'>" + time_desc(s["time"],short=shortTimeDesc) + "</td>"
		if pictures:
			html += """<td class='icon'><div style="background-image:url('""" + scrobbleimages[i] + """')"></div></td>"""
		html += "<td class='artists'>" + artistLinks(s["artists"]) + "</td>"
		html += "<td class='title'>" + trackLink({"artists":s["artists"],"title":s["title"]}) + "</td>"
		# Alternative way: Do it in one cell
		#html += "<td class='title'><span>" + artistLinks(s["artists"]) + "</span> — " + trackLink({"artists":s["artists"],"title":s["title"]}) + "</td>"
		html += "</tr>"

		i += 1
		if max_ is not None and i>=max_:
			break


	html += "</table>"

	return (html,len(scrobbles),representative)


def module_pulse(max_=None,**kwargs):

	kwargs_filter = pickKeys(kwargs,"artist","track","associated")
	kwargs_time = pickKeys(kwargs,"since","to","within","step","stepn","trail")

	ranges = database.get_pulse(**kwargs_time,**kwargs_filter)

	if max_ is not None: ranges = ranges[:max_]

	# if time range not explicitly specified, only show from first appearance
#	if "since" not in kwargs:
#		while ranges[0]["scrobbles"] == 0:
#			del ranges[0]

	maxbar = max([t["scrobbles"] for t in ranges])
	maxbar = max(maxbar,1)

	#build list
	html = "<table class='list'>"
	for t in ranges:
		fromstr = "/".join([str(e) for e in t["from"]])
		tostr = "/".join([str(e) for e in t["to"]])
		html += "<tr>"
		html += "<td>" + range_desc(t["from"],t["to"],short=True) + "</td>"
		html += "<td class='amount'>" + scrobblesLink({"since":fromstr,"to":tostr},amount=t["scrobbles"],**kwargs_filter) + "</td>"
		html += "<td class='bar'>" + scrobblesLink({"since":fromstr,"to":tostr},percent=t["scrobbles"]*100/maxbar,**kwargs_filter) + "</td>"
		html += "</tr>"
	html += "</table>"


	return html

def module_trackcharts(max_=None,**kwargs):

	kwargs_filter = pickKeys(kwargs,"artist","associated")
	kwargs_time = pickKeys(kwargs,"since","to","within")

	tracks = database.get_charts_tracks(**kwargs_filter,**kwargs_time)

	# last time range (to compare)
	if "within" in kwargs_time:
		from malojatime import _get_next
		trackslast = database.get_charts_tracks(**kwargs_filter,within=_get_next(kwargs_time["within"],step=-1))
		# create rank association
		lastrank = {}
		for tl in trackslast:
			lastrank[(*tl["track"]["artists"],tl["track"]["title"])] = tl["rank"]
		for t in tracks:
			try:
				t["delta"] = lastrank[(*t["track"]["artists"],t["track"]["title"])] - t["rank"]
			except:
				t["delta"] = None

	if tracks != []:
		maxbar = tracks[0]["scrobbles"]
		representative = tracks[0]["track"]
	else:
		representative = None


	i = 0
	html = "<table class='list'>"
	for e in tracks:
		i += 1
		if max_ is not None and i>max_:
			break
		html += "<tr>"
		# rank
		if i == 1 or e["scrobbles"] < prev["scrobbles"]:
			html += "<td class='rank'>#" + str(i) + "</td>"
		else:
			html += "<td class='rank'></td>"
		# rank change
		if "within" not in kwargs_time: pass
		elif e["delta"] is None:
			html += "<td class='rankup' title='New'>🆕</td>"
		elif e["delta"] > 0:
			html += "<td class='rankup' title='up from #" + str(e["rank"]+e["delta"]) + "'>↗</td>"
		elif e["delta"] < 0:
			html += "<td class='rankdown' title='down from #" + str(e["rank"]+e["delta"]) + "'>↘</td>"
		else:
			html += "<td class='ranksame' title='Unchanged'>➡</td>"
		# track
		html += "<td class='artists'>" + artistLinks(e["track"]["artists"]) + "</td>"
		html += "<td class='title'>" + trackLink(e["track"]) + "</td>"
		# scrobbles
		html += "<td class='amount'>" + scrobblesTrackLink(e["track"],kwargs_time,amount=e["scrobbles"]) + "</td>"
		html += "<td class='bar'>" + scrobblesTrackLink(e["track"],kwargs_time,percent=e["scrobbles"]*100/maxbar) + "</td>"
		html += "</tr>"
		prev = e
	html += "</table>"

	return (html,representative)


def module_artistcharts(max_=None,**kwargs):

	kwargs_filter = pickKeys(kwargs,"associated") #not used right now
	kwargs_time = pickKeys(kwargs,"since","to","within")

	artists = database.get_charts_artists(**kwargs_filter,**kwargs_time)

	# last time range (to compare)
	if "within" in kwargs_time:
		from malojatime import _get_next
		artistslast = database.get_charts_artists(**kwargs_filter,within=_get_next(kwargs_time["within"],step=-1))
		# create rank association
		lastrank = {}
		for al in artistslast:
			lastrank[al["artist"]] = al["rank"]
		for a in artists:
			try:
				a["delta"] = lastrank[a["artist"]] - a["rank"]
			except:
				a["delta"] = None

	if artists != []:
		maxbar = artists[0]["scrobbles"]
		representative = artists[0]["artist"]
	else:
		representative = None

	i = 0
	html = "<table class='list'>"
	for e in artists:
		i += 1
		if max_ is not None and i>max_:
			break
		html += "<tr>"
		# rank
		if i == 1 or e["scrobbles"] < prev["scrobbles"]:
			html += "<td class='rank'>#" + str(i) + "</td>"
		else:
			html += "<td class='rank'></td>"
		# rank change
		if "within" not in kwargs_time: pass
		elif e["delta"] is None:
			html += "<td class='rankup' title='New'>🆕</td>"
		elif e["delta"] > 0:
			html += "<td class='rankup' title='up from #" + str(e["rank"]+e["delta"]) + "'>↗</td>"
		elif e["delta"] < 0:
			html += "<td class='rankdown' title='down from #" + str(e["rank"]+e["delta"]) + "'>↘</td>"
		else:
			html += "<td class='ranksame' title='Unchanged'>➡</td>"
		# artist
		html += "<td class='artist'>" + artistLink(e["artist"])
		if (e["counting"] != []):
			html += " <span class='extra'>incl. " + ", ".join([artistLink(a) for a in e["counting"]]) + "</span>"
		html += "</td>"
		# scrobbles
		html += "<td class='amount'>" + scrobblesArtistLink(e["artist"],kwargs_time,amount=e["scrobbles"],associated=True) + "</td>"
		html += "<td class='bar'>" + scrobblesArtistLink(e["artist"],kwargs_time,percent=e["scrobbles"]*100/maxbar,associated=True) + "</td>"
		html += "</tr>"
		prev = e

	html += "</table>"

	return (html, representative)



def module_toptracks(pictures=True,**kwargs):

	kwargs_filter = pickKeys(kwargs,"artist","associated")
	kwargs_time = pickKeys(kwargs,"since","to","within","step","stepn","trail")

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

		fromstr = "/".join([str(p) for p in e["from"]])
		tostr = "/".join([str(p) for p in e["to"]])

		i += 1
		html += "<tr>"


		html += "<td>" + range_desc(e["from"],e["to"],short=True) + "</td>"
		if e["track"] is None:
			if pictures:
				html += "<td><div></div></td>"
			html += "<td class='stats'>" + "No scrobbles" + "</td>"
			html += "<td>" + "" + "</td>"
			html += "<td class='amount'>" + "0" + "</td>"
			html += "<td class='bar'>" + "" + "</td>"
		else:
			if pictures:
				html += """<td class='icon'><div style="background-image:url('""" + getTrackImage(e["track"]["artists"],e["track"]["title"],fast=True) + """')"></div></td>"""
			html += "<td class='artists'>" + artistLinks(e["track"]["artists"]) + "</td>"
			html += "<td class='title'>" + trackLink(e["track"]) + "</td>"
			html += "<td class='amount'>" + scrobblesTrackLink(e["track"],{"since":fromstr,"to":tostr},amount=e["scrobbles"]) + "</td>"
			html += "<td class='bar'>" + scrobblesTrackLink(e["track"],{"since":fromstr,"to":tostr},percent=e["scrobbles"]*100/maxbar) + "</td>"
		html += "</tr>"
		prev = e
	html += "</table>"

	return (html,representative)

def module_topartists(pictures=True,**kwargs):

	kwargs_time = pickKeys(kwargs,"since","to","within","step","stepn","trail")

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

		fromstr = "/".join([str(p) for p in e["from"]])
		tostr = "/".join([str(p) for p in e["to"]])

		i += 1
		html += "<tr>"


		html += "<td>" + range_desc(e["from"],e["to"],short=True) + "</td>"

		if e["artist"] is None:
			if pictures:
				html += "<td><div></div></td>"
			html += "<td class='stats'>" + "No scrobbles" + "</td>"
			html += "<td class='amount'>" + "0" + "</td>"
			html += "<td class='bar'>" + "" + "</td>"
		else:
			if pictures:
				html += """<td class='icon'><div style="background-image:url('""" + getArtistImage(e["artist"],fast=True) + """')"></div></td>"""
			html += "<td class='artist'>" + artistLink(e["artist"])
			if (e["counting"] != []):
				html += " <span class='extra'>incl. " + ", ".join([artistLink(a) for a in e["counting"]]) + "</span>"
			html += "</td>"
			html += "<td class='amount'>" + scrobblesArtistLink(e["artist"],{"since":fromstr,"to":tostr},amount=e["scrobbles"],associated=True) + "</td>"
			html += "<td class='bar'>" + scrobblesArtistLink(e["artist"],{"since":fromstr,"to":tostr},percent=e["scrobbles"]*100/maxbar,associated=True) + "</td>"
		html += "</tr>"
		prev = e
	html += "</table>"

	return (html,representative)


def module_artistcharts_tiles(**kwargs):

	kwargs_filter = pickKeys(kwargs,"associated") #not used right now
	kwargs_time = pickKeys(kwargs,"since","to","within")

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
			#rank = i if e["scrobbles"] != rnk[1] else rnk[0]
			#rnk = (rank,e["scrobbles"])
			rank = "#" + str(e["rank"])
			#image = "/image?artist=" + urllib.parse.quote(e["artist"])
			image = getArtistImage(e["artist"],fast=True)
			link = artistLink(e["artist"])
		else:
			rank = ""
			image = ""
			link = ""


		html += """<td style="background-image:url('""" + image + """')"><span class="stats">""" + rank + "</span> <span>" + link + "</span></td>"

		i += 1

		if i in smallpart:
			html += "</tr>"

		if i in bigpart:
			html += "</table></td>"

	html += """</tr></table>"""

	return html


def module_trackcharts_tiles(**kwargs):

	kwargs_filter = pickKeys(kwargs,"artist","associated")
	kwargs_time = pickKeys(kwargs,"since","to","within")

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
			#rank = i if e["scrobbles"] != rnk[1] else rnk[0]
			#rnk = (rank,e["scrobbles"])
			rank = "#" + str(e["rank"])
			#image = "/image?title=" + urllib.parse.quote(e["track"]["title"]) + "&" + "&".join(["artist=" + urllib.parse.quote(a) for a in e["track"]["artists"]])
			image = getTrackImage(e["track"]["artists"],e["track"]["title"],fast=True)
			link = trackLink(e["track"])
		else:
			rank = ""
			image = ""
			link = ""

		html += """<td style="background-image:url('""" + image + """')"><span class="stats">""" + rank + "</span> <span>" + link + "</span></td>"

		i += 1

		if i in smallpart:
			html += "</tr>"

		if i in bigpart:
			html += "</table></td>"

	html += """</tr></table>"""

	return html



def module_filterselection(keys,time=True,delimit=False):
	# all other keys that will not be changed by clicking another filter


	html = ""


	if time:

		keystr = "?" + keysToUrl(keys,exclude=["since","to","in"])


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



		html += "<div>"
		if keys.get("since") == "today" or keys.get("in") == "today":
			html += "<span class='stat_selector' style='opacity:0.5;'>Today</span>"
		else:
			html += "<a href='" + keystr + "&since=today'><span class='stat_selector'>Today</span></a>"
		html += " | "

		if keys.get("since") == "sunday":
			html += "<span class='stat_selector' style='opacity:0.5;'>This Week</span>"
		else:
			html += "<a href='" + keystr + "&since=sunday'><span class='stat_selector'>This Week</span></a>"
		html += " | "

		if keys.get("since") == "month" or keys.get("in") == "month":
			html += "<span class='stat_selector' style='opacity:0.5;'>This Month</span>"
		else:
			html += "<a href='" + keystr + "&since=month'><span class='stat_selector'>This Month</span></a>"
		html += " | "

		if keys.get("since") == "year" or keys.get("in") == "year":
			html += "<span class='stat_selector' style='opacity:0.5;'>This Year</span>"
		else:
			html += "<a href='" + keystr + "&since=year'><span class='stat_selector'>This Year</span></a>"
		html += " | "

		if keys.get("since") is None and keys.get("in") is None:
			html += "<span class='stat_selector' style='opacity:0.5;'>All Time</span>"
		else:
			html += "<a href='" + keystr + "'><span class='stat_selector'>All Time</span></a>"

		html += "</div>"

	if delimit:

		keystr = "?" + keysToUrl(keys,exclude=["step","stepn"])

		html += "<div>"
		if keys.get("step") == "day":
			html += "<span class='stat_selector' style='opacity:0.5;'>Daily</span>"
		else:
			html += "<a href='" + keystr + "&step=day'><span class='stat_selector'>Daily</span></a>"
		html += " | "

		if keys.get("step") == "month" or keys.get("step") is None:
			html += "<span class='stat_selector' style='opacity:0.5;'>Monthly</span>"
		else:
			html += "<a href='" + keystr + "&step=month'><span class='stat_selector'>Monthly</span></a>"
		html += " | "

		if keys.get("step") == "year":
			html += "<span class='stat_selector' style='opacity:0.5;'>Yearly</span>"
		else:
			html += "<a href='" + keystr + "&step=year'><span class='stat_selector'>Yearly</span></a>"

		html += "</div>"



		keystr = "?" + keysToUrl(keys,exclude=["trail"])

		html += "<div>"
		if keys.get("trail") == "1" or keys.get("trail") is None:
			html += "<span class='stat_selector' style='opacity:0.5;'>Standard</span>"
		else:
			html += "<a href='" + keystr + "'><span class='stat_selector'>Standard</span></a>"
		html += " | "

		if keys.get("trail") == "2":
			html += "<span class='stat_selector' style='opacity:0.5;'>Trailing</span>"
		else:
			html += "<a href='" + keystr + "&trail=2'><span class='stat_selector'>Trailing</span></a>"
		html += " | "

		if keys.get("trail") == "3":
			html += "<span class='stat_selector' style='opacity:0.5;'>Long Trailing</span>"
		else:
			html += "<a href='" + keystr + "&trail=3'><span class='stat_selector'>Long Trailing</span></a>"

		html += "</div>"

	return html
