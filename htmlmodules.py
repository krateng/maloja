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
def module_scrobblelist(max_=None,pictures=False,shortTimeDesc=False,**kwargs):
	
	kwargs_filter = pickKeys(kwargs,"artist","track","associated")
	kwargs_time = pickKeys(kwargs,"since","to","within")
	
	scrobbles = database.get_scrobbles(**kwargs_time,**kwargs_filter) #we're getting all scrobbles for the number and only filtering them on site
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
		html += "<td class='rank'>#" + str(i) + "</td>"
		html += "<td class='artists'>" + artistLinks(e["track"]["artists"]) + "</td>"
		html += "<td class='title'>" + trackLink(e["track"]) + "</td>"
		html += "<td class='amount'>" + scrobblesTrackLink(e["track"],kwargs_time,amount=e["scrobbles"]) + "</td>"
		html += "<td class='bar'>" + scrobblesTrackLink(e["track"],kwargs_time,percent=e["scrobbles"]*100/maxbar) + "</td>"
		html += "</tr>"
	html += "</table>"
	
	return (html,representative)
	
	
def module_artistcharts(max_=None,**kwargs):

	kwargs_filter = pickKeys(kwargs,"associated") #not used right now
	kwargs_time = pickKeys(kwargs,"since","to","within")
	
	artists = database.get_charts_artists(**kwargs_filter,**kwargs_time)
	
	
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
		html += "<td class='rank'>#" + str(i) + "</td>"
		html += "<td class='artist'>" + artistLink(e["artist"])
		if (e["counting"] != []):
			html += " <span class='extra'>incl. " + ", ".join([artistLink(a) for a in e["counting"]]) + "</span>"
		html += "</td>"
		html += "<td class='amount'>" + scrobblesArtistLink(e["artist"],kwargs_time,amount=e["scrobbles"],associated=True) + "</td>"
		html += "<td class='bar'>" + scrobblesArtistLink(e["artist"],kwargs_time,percent=e["scrobbles"]*100/maxbar,associated=True) + "</td>"
		html += "</tr>"

	html += "</table>"
	
	return (html, representative)
	
	
def module_artistcharts_tiles(**kwargs):

	kwargs_filter = pickKeys(kwargs,"associated") #not used right now
	kwargs_time = pickKeys(kwargs,"since","to","within")
	
	artists = database.get_charts_artists(**kwargs_filter,**kwargs_time)[:14]
	while len(artists)<14: artists.append(None)
	
	i = 1
	
	bigpart = [0,1,2,6,15]
	smallpart = [0,1,2,4,6,9,12,15]
	rnk = (0,0) #temporary store so entries with the same scrobble amount get the same rank
	
	html = """<table class="tiles_top"><tr>"""
		
	for e in artists:
		
		
		if i in bigpart:
			n = bigpart.index(i)
			html += """<td><table class="tiles_""" + str(n) + """x""" + str(n) + """ tiles_sub">"""
			
		if i in smallpart:
			html += "<tr>"
		
		
		if e is not None:
			rank = i if e["scrobbles"] != rnk[1] else rnk[0]
			rnk = (rank,e["scrobbles"])
			rank = "#" + str(rank)
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
	rnk = (0,0) #temporary store so entries with the same scrobble amount get the same rank
	
	
	html = """<table class="tiles_top"><tr>"""
		
	for e in tracks:
		
		
		if i in bigpart:
			n = bigpart.index(i)
			html += """<td><table class="tiles_""" + str(n) + """x""" + str(n) + """ tiles_sub">"""
			
		if i in smallpart:
			html += "<tr>"
		
		
		if e is not None:
			rank = i if e["scrobbles"] != rnk[1] else rnk[0]
			rnk = (rank,e["scrobbles"])
			rank = "#" + str(rank)
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

