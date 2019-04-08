import urllib
from bottle import FormsDict
import datetime
from urihandler import compose_querystring


# returns the proper column(s) for an artist or track
def entity_column(element,counting=[],image=None):

	html = ""

	if image is not None:
		html += """<td class='icon'><div style="background-image:url('""" + image + """')"></div></td>"""

	if "artists" in element:
		# track
		html += "<td class='artists'>" + artistLinks(element["artists"]) + "</td>"
		html += "<td class='title'>" + trackLink({"artists":element["artists"],"title":element["title"]}) + "</td>"
	else:
		# artist
		html += "<td class='artist'>" + artistLink(element)
		if (counting != []):
			html += " <span class='extra'>incl. " + ", ".join([artistLink(a) for a in counting]) + "</span>"
		html += "</td>"

	return html

def artistLink(name):
	return "<a href='/artist?artist=" + urllib.parse.quote(name) + "'>" + name + "</a>"

def artistLinks(artists):
	return ", ".join([artistLink(a) for a in artists])

#def trackLink(artists,title):
def trackLink(track):
	artists,title = track["artists"],track["title"]
	return "<a href='/track?title=" + urllib.parse.quote(title) + "&" + "&".join(["artist=" + urllib.parse.quote(a) for a in artists]) + "'>" + title + "</a>"

#def scrobblesTrackLink(artists,title,timekeys,amount=None,pixels=None):
def scrobblesTrackLink(track,timekeys,amount=None,percent=None):
	artists,title = track["artists"],track["title"]
	inner = str(amount) if amount is not None else "<div style='width:" + str(percent) + "%;'></div>"
	return "<a href='/scrobbles?" + "&".join(["artist=" + urllib.parse.quote(a) for a in artists]) + "&title=" + urllib.parse.quote(title) + "&" + compose_querystring(timekeys) + "'>" + inner + "</a>"

def scrobblesArtistLink(artist,timekeys,amount=None,percent=None,associated=False):
	inner = str(amount) if amount is not None else "<div style='width:" + str(percent) + "%;'></div>"
	askey = "&associated" if associated else ""
	return "<a href='/scrobbles?artist=" + urllib.parse.quote(artist) + "&" + compose_querystring(timekeys) + askey + "'>" + inner + "</a>"

def scrobblesLink(timekeys,amount=None,percent=None,artist=None,track=None,associated=False):
	if track is not None: return scrobblesTrackLink(track,timekeys,amount,percent)
	if artist is not None: return scrobblesArtistLink(artist,timekeys,amount,percent,associated)
	inner = str(amount) if amount is not None else "<div style='width:" + str(percent) + "%;'></div>"
	return "<a href='/scrobbles?" + compose_querystring(timekeys) + "'>" + inner + "</a>"



# limit a multidict to only the specified keys
# would be a simple constructor expression, but multidicts apparently don't let me do that
def pickKeys(d,*keys):
	if isinstance(d,dict):
		return {k:d.get(k) for k in d if k in keys}
	else:
		# create a normal dictionary of lists
		newd = {k:d.getall(k) for k in d if k in keys}
		# one by one add the list entries to the formsdict
		finald = FormsDict()
		for k in newd:
			for v in newd.get(k):
				finald.append(k,v)

		return finald
