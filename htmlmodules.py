from htmlgenerators import *
import database
from utilities import getArtistsInfo, getTracksInfo
import urllib


def getpictures(ls,result,tracks=False):
	from utilities import getArtistsInfo, getTracksInfo
	if tracks:
		for element in getTracksInfo(ls):
			result.append(element.get("image"))
	else:
		for element in getArtistsInfo(ls):
			result.append(element.get("image"))


# artist=None,track=None,since=None,to=None,within=None,associated=False,max_=None,pictures=False
def module_scrobblelist(max_=None,pictures=False,shortTimeDesc=False,**kwargs):
	
	kwargs_filter = pickKeys(kwargs,"artist","track","associated")
	kwargs_time = pickKeys(kwargs,"since","to","within")
	
	scrobbles = database.get_scrobbles(**kwargs_time,**kwargs_filter) #we're getting all scrobbles for the number and only filtering them on site
	if pictures:
		scrobbleswithpictures = scrobbles if max_ is None else scrobbles[:max_]
		#scrobbleimages = [e.get("image") for e in getTracksInfo(scrobbleswithpictures)] #will still work with scrobble objects as they are a technically a subset of track objects
		scrobbleimages = ["/image?title=" + urllib.parse.quote(t["title"]) + "&" + "&".join(["artist=" + urllib.parse.quote(a) for a in t["artists"]])  for t in scrobbleswithpictures]
	
	representative = scrobbles[0] if scrobbles is not [] else None
	
	# build list
	i = 0
	html = "<table class='list'>"
	for s in scrobbles:
		i += 1
		if max_ is not None and i>=max_:
			break
			
		html += "<tr>"
		html += "<td class='time'>" + getTimeDesc(s["time"],short=shortTimeDesc) + "</td>"
		if pictures:
			html += """<td class='icon'><div style="background-image:url('""" + scrobbleimages[i] + """')"></div></td>"""
		html += "<td class='artists'>" + artistLinks(s["artists"]) + "</td>"
		html += "<td class='title'>" + trackLink({"artists":s["artists"],"title":s["title"]}) + "</td>"
		html += "</tr>"
		
		
	html += "</table>"
	
	return (html,len(scrobbles),representative)
	
	
def module_pulse(max_=None,**kwargs):

	kwargs_filter = pickKeys(kwargs,"artist","track","associated")
	kwargs_time = pickKeys(kwargs,"since","to","within","step","stepn","trail")
	
	ranges = database.get_pulse(**kwargs_time,**kwargs_filter)
	
	maxbar = max([t["scrobbles"] for t in ranges])
	maxbar = max(maxbar,1)
	
	#build list
	html = "<table class='list'>"
	for t in ranges:
		fromstr = "/".join([str(e) for e in t["from"]])
		tostr = "/".join([str(e) for e in t["to"]])
		html += "<tr>"
		html += "<td>" + getRangeDesc(t["from"],t["to"]) + "</td>"
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
