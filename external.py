import urllib.parse, urllib.request
import json
from doreah.settings import get_settings
from doreah.logging import log


apis_artists = [
	{
		"name":"LastFM + Fanart.tv",
		"check":get_settings("LASTFM_API_KEY") is not None and get_settings("FANARTTV_API_KEY") is not None,
		"steps":[
			("url","http://ws.audioscrobbler.com/2.0/?method=artist.getinfo&artist={artiststring}&api_key=" + get_settings("LASTFM_API_KEY") + "&format=json"),
			("parse",["artist","mbid"]),
			("url","http://webservice.fanart.tv/v3/music/{var}?api_key=" + get_settings("FANARTTV_API_KEY")),
			("parse",["artistthumb",0,"url"])
		]
	}
]

apis_tracks = [
	{
		"name":"LastFM",
		"check":get_settings("LASTFM_API_KEY") is not None,
		"steps":[
			("url","https://ws.audioscrobbler.com/2.0/?method=track.getinfo&track={titlestring}&artist={artiststring}&api_key=" + get_settings("LASTFM_API_KEY") + "&format=json"),
			("parse",["track","album","image",3,"#text"])
		]
	}
]

def api_request_artist(artist):
	for api in apis_artists:
		if api["check"]:
			log("API: " + api["name"] + "; Image request: " + artist,module="external")
			try:
				artiststring = urllib.parse.quote(artist)
				var = artiststring
				for step in api["steps"]:
					if step[0] == "url":
						response = urllib.request.urlopen(step[1].format(artiststring=artiststring,var=var))
						var = json.loads(response.read())
					elif step[0] == "parse":
						for node in step[1]:
							var = var[node]
				assert isinstance(var,str) and var != ""
			except:
				continue

			return var
		else:
			pass
	return None

def api_request_track(track):
	artists, title = track
	for api in apis_tracks:
		if api["check"]:
			log("API: " + api["name"] + "; Image request: " + "/".join(artists) + " - " + title,module="external")
			try:
				artiststring = urllib.parse.quote(", ".join(artists))
				titlestring = urllib.parse.quote(title)
				var = artiststring + titlestring
				for step in api["steps"]:
					if step[0] == "url":
						response = urllib.request.urlopen(step[1].format(artiststring=artiststring,titlestring=titlestring,var=var))
						var = json.loads(response.read())
					elif step[0] == "parse":
						for node in step[1]:
							var = var[node]
				assert isinstance(var,str) and var != ""
			except:
				if len(artists) == 1: return None
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
