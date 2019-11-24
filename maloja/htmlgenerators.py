import urllib
from bottle import FormsDict
import datetime
from .urihandler import compose_querystring
import urllib.parse
from doreah.settings import get_settings


# returns the proper column(s) for an artist or track
def entity_column(element,counting=[],image=None):

	html = ""

	if image is not None:
		html += """<td class='icon'><div style="background-image:url('""" + image + """')"></div></td>"""

	if "artists" in element:
		# track
	#	html += "<td class='artists'>" + html_links(element["artists"]) + "</td>"
	#	html += "<td class='title'>" + html_link(element) + "</td>"
		html += "<td class='track'><span class='artist_in_trackcolumn'>"
		html += trackSearchLink(element)
		html += html_links(element["artists"]) + "</span> – " + html_link(element) + "</td>"
	else:
		# artist
		html += "<td class='artist'>" + html_link(element)
		if (counting != []):
			html += " <span class='extra'>incl. " + html_links(counting) + "</span>"
		html += "</td>"

	return html

def uri_query(entity):
	if "artists" in entity:
		#track
		return "title=" + urllib.parse.quote(entity["title"]) \
			+ "&" + "&".join(["artist=" + urllib.parse.quote(a) for a in entity["artists"]])

	else:
		#artist
		return "artist=" + urllib.parse.quote(entity)

# returns the address of the track / artist page
def link_address(entity):
	if "artists" in entity:
		#track
		return "/track?" + uri_query(entity)
	else:
		#artist
		return "/artist?" + uri_query(entity)

#returns linked name
def html_link(entity):
	if "artists" in entity:
		#track
		name = entity["title"]
	else:
		#artist
		name = entity
	return "<a href='" + link_address(entity) + "'>" + name + "</a>"

def html_links(entities):
	return ", ".join([html_link(e) for e in entities])

# DEPRECATED
def artistLink(name):
	return html_link(name)
	#return "<a href='/artist?artist=" + urllib.parse.quote(name) + "'>" + name + "</a>"

# DEPRECATED
def artistLinks(artists):
	return ", ".join([artistLink(a) for a in artists])

#def trackLink(artists,title):
# DEPRECATED
def trackLink(track):
	return html_link(track)
	#artists,title = track["artists"],track["title"]
	#return "<a href='/track?title=" + urllib.parse.quote(title) + "&" + "&".join(["artist=" + urllib.parse.quote(a) for a in artists]) + "'>" + title + "</a>"

def trackSearchLink(track):
	searchProvider = get_settings("TRACK_SEARCH_PROVIDER")
	if searchProvider is None: return ""

	link = "<a class='trackProviderSearch' href='"
	if searchProvider == "YouTube":
		link += "https://www.youtube.com/results?search_query="
	elif searchProvider == "YouTube Music":
		link += "https://music.youtube.com/search?q="
	elif searchProvider == "Google Play Music":
		link += "https://play.google.com/music/listen#/srs/"
	elif searchProvider == "Spotify":
		link += "https://open.spotify.com/search/results/"
	elif searchProvider == "Tidal":
		link += "https://listen.tidal.com/search/tracks?q="
	elif searchProvider == "SoundCloud":
		link += "https://soundcloud.com/search?q="
	elif searchProvider == "Amazon Music":
		link += "https://music.amazon.com/search/"
	elif searchProvider == "Deezer":
		link += "https://www.deezer.com/search/"
	else:
		link += "https://www.google.com/search?q=" # ¯\_(ツ)_/¯

	link += urllib.parse.quote(", ".join(track["artists"]) + " " + track["title"]) + "'>&#127925;</a>"
	return link

#def scrobblesTrackLink(artists,title,timekeys,amount=None,pixels=None):
def scrobblesTrackLink(track,timekeys,amount=None,percent=None):
	artists,title = track["artists"],track["title"]
	inner = str(amount) if amount is not None else "<div style='width:" + str(percent) + "%;'></div>"
	return "<a href='/scrobbles?" + uri_query(track) + "&" + compose_querystring(timekeys) + "'>" + inner + "</a>"

def scrobblesArtistLink(artist,timekeys,amount=None,percent=None,associated=False):
	inner = str(amount) if amount is not None else "<div style='width:" + str(percent) + "%;'></div>"
	askey = "&associated" if associated else ""
	return "<a href='/scrobbles?" + uri_query(artist) + "&" + compose_querystring(timekeys) + askey + "'>" + inner + "</a>"

def scrobblesLink(timekeys,amount=None,percent=None,artist=None,track=None,associated=False):
	if track is not None: return scrobblesTrackLink(track,timekeys,amount,percent)
	if artist is not None: return scrobblesArtistLink(artist,timekeys,amount,percent,associated)
	inner = str(amount) if amount is not None else "<div style='width:" + str(percent) + "%;'></div>"
	return "<a href='/scrobbles?" + compose_querystring(timekeys) + "'>" + inner + "</a>"



def rankTrackLink(track,timekeys,rank=None,percent=None,medal=None):
	cl = ""
	if medal == 1: cl = "class='gold'"
	if medal == 2: cl = "class='silver'"
	if medal == 3: cl = "class='bronze'"
	inner = str(rank) if rank is not None else "<div " + cl + " style='width:" + str(percent) + "%;'></div>"

	return "<a href='/charts_tracks?" + compose_querystring(timekeys) + "'>" + inner + "</a>"

def rankArtistLink(artist,timekeys,rank=None,percent=None,medal=None):
	cl = ""
	if medal == 1: cl = "class='gold'"
	if medal == 2: cl = "class='silver'"
	if medal == 3: cl = "class='bronze'"
	inner = str(rank) if rank is not None else "<div " + cl + " style='width:" + str(percent) + "%;'></div>"
	return "<a href='/charts_artists?" + compose_querystring(timekeys) + "'>" + inner + "</a>"

def rankLink(timekeys,rank=None,percent=None,artist=None,track=None,medal=None):
	if track is not None: return rankTrackLink(track,timekeys,rank,percent,medal)
	if artist is not None: return rankArtistLink(artist,timekeys,rank,percent,medal)



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
