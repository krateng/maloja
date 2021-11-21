from . import MetadataInterface, utf, b64
import urllib.parse, urllib.request
import json
from threading import Timer
from doreah.logging import log

class Spotify(MetadataInterface):
	name = "Spotify"
	identifier = "spotify"

	settings = {
		"apiid":"SPOTIFY_API_ID",
		"secret":"SPOTIFY_API_SECRET"
	}

	metadata = {
		"trackurl": "https://api.spotify.com/v1/search?q=artist:{artist}%20track:{title}&type=track&access_token={token}",
		"artisturl": "https://api.spotify.com/v1/search?q=artist:{artist}&type=artist&access_token={token}",
		"response_type":"json",
		"response_parse_tree_track": ["tracks","items",0,"album","images",0,"url"],
		"response_parse_tree_artist": ["artists","items",0,"images",0,"url"],
		"required_settings": ["apiid","secret"],
	}

	def authorize(self):

		if self.active_metadata():

			try:
				keys = {
					"url":"https://accounts.spotify.com/api/token",
					"method":"POST",
					"headers":{
						"Authorization":"Basic " + b64(utf(self.settings["apiid"] + ":" + self.settings["secret"])).decode("utf-8")
					},
					"data":bytes(urllib.parse.urlencode({"grant_type":"client_credentials"}),encoding="utf-8")
				}
				req = urllib.request.Request(**keys)
				response = urllib.request.urlopen(req)
				responsedata = json.loads(response.read())
				if "error" in responsedata:
					log("Error authenticating with Spotify: " + responsedata['error_description'])
					expire = 3600
				else:
					expire = responsedata.get("expires_in",3600)
					self.settings["token"] = responsedata["access_token"]
					log("Successfully authenticated with Spotify")
				Timer(expire,self.authorize).start()
			except Exception as e:
				log("Error while authenticating with Spotify: " + repr(e))
