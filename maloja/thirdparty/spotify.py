from . import MetadataInterface, utf, b64
import requests
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
		"trackurl": "https://api.spotify.com/v1/search?q={title}%20artist:{artist}&type=track&access_token={token}",
		"albumurl": "https://api.spotify.com/v1/search?q={title}%20artist:{artist}&type=album&access_token={token}",
		"artisturl": "https://api.spotify.com/v1/search?q={artist}&type=artist&access_token={token}",
		"response_type":"json",
		"response_parse_tree_track": ["tracks","items",0,"album","images",0,"url"], # use album art
		"response_parse_tree_album": ["albums","items",0,"images",0,"url"],
		"response_parse_tree_artist": ["artists","items",0,"images",0,"url"],
		"required_settings": ["apiid","secret"],
		"enabled_entity_types": ["artist","album","track"]
	}

	def authorize(self):

		if self.active_metadata():

			try:
				keys = {
					"url":"https://accounts.spotify.com/api/token",
					"headers":{
						"Authorization":"Basic " + b64(utf(self.settings["apiid"] + ":" + self.settings["secret"])).decode("utf-8"),
						"User-Agent": self.useragent
					},
					"data":{"grant_type":"client_credentials"}
				}
				res = requests.post(**keys)
				responsedata = res.json()
				if "error" in responsedata:
					log("Error authenticating with Spotify: " + responsedata['error_description'])
					expire = 3600
				else:
					expire = responsedata.get("expires_in",3600)
					self.settings["token"] = responsedata["access_token"]
					#log("Successfully authenticated with Spotify")
				t = Timer(expire,self.authorize)
				t.daemon = True
				t.start()
			except Exception as e:
				log("Error while authenticating with Spotify: " + repr(e))

	def handle_json_result_error(self,result):
		result = result.get('tracks') or result.get('albums') or result.get('artists')
		if not result['items']:
			return True