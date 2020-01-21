import urllib.parse, urllib.request
import json
import base64
from doreah.settings import get_settings
from doreah.logging import log
import hashlib
import xml.etree.ElementTree as ET

### PICTURES


apis_artists = []

if get_settings("LASTFM_API_KEY") not in [None,"ASK"] and get_settings("FANARTTV_API_KEY") not in [None,"ASK"]:
	apis_artists.append({
		"name":"LastFM + Fanart.tv",
		#"check":get_settings("LASTFM_API_KEY") not in [None,"ASK"] and get_settings("FANARTTV_API_KEY") not in [None,"ASK"],
		"steps":[
			("get","http://ws.audioscrobbler.com/2.0/?method=artist.getinfo&artist={artiststring}&api_key=" + str(get_settings("LASTFM_API_KEY")) + "&format=json"),
			("parse",["artist","mbid"]),
			("get","http://webservice.fanart.tv/v3/music/{var}?api_key=" + str(get_settings("FANARTTV_API_KEY"))),
			("parse",["artistthumb",0,"url"])
		]
	})

if get_settings("SPOTIFY_API_ID") not in [None,"ASK"] and get_settings("SPOTIFY_API_SECRET") not in [None,"ASK"]:
	apis_artists.append({
		"name":"Spotify",
		#"check":get_settings("SPOTIFY_API_ID") not in [None,"ASK"] and get_settings("SPOTIFY_API_SECRET") not in [None,"ASK"],
		"steps":[
			("post","https://accounts.spotify.com/api/token",{"Authorization":"Basic " + base64.b64encode(bytes(get_settings("SPOTIFY_API_ID") + ":" + get_settings("SPOTIFY_API_SECRET"),encoding="utf-8")).decode("utf-8")},{"grant_type":"client_credentials"}),
			("parse",["access_token"]),
			("get","https://api.spotify.com/v1/search?q={artiststring}&type=artist&access_token={var}"),
			("parse",["artists","items",0,"images",0,"url"])
		]
	})

apis_tracks = []

if get_settings("LASTFM_API_KEY") not in [None,"ASK"]:
	apis_tracks.append({
		"name":"LastFM",
		#"check":get_settings("LASTFM_API_KEY") not in [None,"ASK"],
		"steps":[
			("get","https://ws.audioscrobbler.com/2.0/?method=track.getinfo&track={titlestring}&artist={artiststring}&api_key=" + get_settings("LASTFM_API_KEY") + "&format=json"),
			("parse",["track","album","image",3,"#text"])
		]
	})

if get_settings("SPOTIFY_API_ID") not in [None,"ASK"] and get_settings("SPOTIFY_API_SECRET") not in [None,"ASK"]:
	apis_tracks.append({
		"name":"Spotify",
		#"check":get_settings("SPOTIFY_API_ID") not in [None,"ASK"] and get_settings("SPOTIFY_API_SECRET") not in [None,"ASK"],
		"steps":[
			("post","https://accounts.spotify.com/api/token",{"Authorization":"Basic " + base64.b64encode(bytes(get_settings("SPOTIFY_API_ID") + ":" + get_settings("SPOTIFY_API_SECRET"),encoding="utf-8")).decode("utf-8")},{"grant_type":"client_credentials"}),
			("parse",["access_token"]),
			("get","https://api.spotify.com/v1/search?q={artiststring}%20{titlestring}&type=track&access_token={var}"),
			("parse",["tracks","items",0,"album","images",0,"url"])
		]
	})


def api_request_artist(artist):
	for api in apis_artists:
		if True:
			try:
				artiststring = urllib.parse.quote(artist)
				var = artiststring
				for step in api["steps"]:
					if step[0] == "get":
						response = urllib.request.urlopen(step[1].format(artiststring=artiststring,var=var))
						var = json.loads(response.read())
					elif step[0] == "post":
						keys = {
							"url":step[1].format(artiststring=artiststring,var=var),
							"method":"POST",
							"headers":step[2],
							"data":bytes(urllib.parse.urlencode(step[3]),encoding="utf-8")
						}
						req = urllib.request.Request(**keys)
						response = urllib.request.urlopen(req)
						var = json.loads(response.read())
					elif step[0] == "parse":
						for node in step[1]:
							var = var[node]
				assert isinstance(var,str) and var != ""
			except Exception as e:
				log("Error while getting artist image from " + api["name"],module="external")
				log(str(e),module="external")
				continue

			return var
		else:
			pass
	return None

def api_request_track(track):
	artists, title = track
	for api in apis_tracks:
		if True:
			try:
				artiststring = urllib.parse.quote(", ".join(artists))
				titlestring = urllib.parse.quote(title)
				var = artiststring + titlestring
				for step in api["steps"]:
					if step[0] == "get":
						response = urllib.request.urlopen(step[1].format(artiststring=artiststring,titlestring=titlestring,var=var))
						var = json.loads(response.read())
					elif step[0] == "post":
						keys = {
							"url":step[1].format(artiststring=artiststring,titlestring=titlestring,var=var),
							"method":"POST",
							"headers":step[2],
							"data":bytes(urllib.parse.urlencode(step[3]),encoding="utf-8")
						}
						req = urllib.request.Request(**keys)
						response = urllib.request.urlopen(req)
						var = json.loads(response.read())
					elif step[0] == "parse":
						for node in step[1]:
							var = var[node]
				assert isinstance(var,str) and var != ""
			except:
				if len(artists) != 1:
					# try the same track with every single artist
					for a in artists:
						result = api_request_track(([a],title))
						if result is not None:
							return result
				continue

			return var
		else:
			pass

	return None








### SCROBBLING

# creates signature and returns full query string
def lfmbuild(parameters):
	m = hashlib.md5()
	keys = sorted(str(k) for k in parameters)
	m.update(utf("".join(str(k) + str(parameters[k]) for k in keys)))
	m.update(utf(get_settings("LASTFM_API_SECRET")))
	sig = m.hexdigest()
	return urllib.parse.urlencode(parameters) + "&api_sig=" + sig

def utf(st):
	return st.encode(encoding="UTF-8")



apis_scrobble = []

if get_settings("LASTFM_API_SK") not in [None,"ASK"] and get_settings("LASTFM_API_SECRET") not in [None,"ASK"] and get_settings("LASTFM_API_KEY") not in [None,"ASK"]:
	apis_scrobble.append({
		"name":"LastFM",
		"scrobbleurl":"http://ws.audioscrobbler.com/2.0/",
		"requestbody":lambda artists,title,timestamp: lfmbuild({"method":"track.scrobble","artist[0]":", ".join(artists),"track[0]":title,"timestamp":timestamp,"api_key":get_settings("LASTFM_API_KEY"),"sk":get_settings("LASTFM_API_SK")})
	})




def proxy_scrobble(artists,title,timestamp):
	for api in apis_scrobble:
		response = urllib.request.urlopen(api["scrobbleurl"],data=utf(api["requestbody"](artists,title,timestamp)))
		xml = response.read()
		data = ET.fromstring(xml)
		if data.attrib.get("status") == "ok":
			if data.find("scrobbles").attrib.get("ignored") == "0":
				log(api["name"] + ": Scrobble accepted: " + "/".join(artists) + " - " + title)
			else:
				log(api["name"] + ": Scrobble not accepted: " + "/".join(artists) + " - " + title)
