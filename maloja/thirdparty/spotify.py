from . import MetadataInterface, utf, b64
import requests
import urllib.parse
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
		"trackurl": "https://api.spotify.com/v1/search?q={title}%20artist:{artist}&type=track",
		"albumurl": "https://api.spotify.com/v1/search?q={title}%20artist:{artist}&type=album",
		"artisturl": "https://api.spotify.com/v1/search?q={artist}&type=artist",
		"response_type":"json",
		"response_parse_tree_track": ["tracks","items",0,"album","images",0,"url"], # use album art
		"response_parse_tree_album": ["albums","items",0,"images",0,"url"],
		"response_parse_tree_artist": ["artists","items",0,"images",0,"url"],
		"required_settings": ["apiid","secret"],
		"enabled_entity_types": ["artist","album","track"],
		"allowed_image_domains": [
			"i.scdn.co",
		]
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

	# Spotify's Web API no longer accepts the access token as an "access_token"
	# query parameter on /v1/search - it must be sent as an Authorization header.
	# Requests made the old way get rejected, which is why these are overridden
	# here instead of relying on the generic MetadataInterface implementation.
	def _auth_headers(self):
		return {
			"User-Agent": self.useragent,
			"Authorization": "Bearer " + (self.settings.get("token") or "")
		}

	def get_image_track(self,track):
		artists, title = track
		artiststring = urllib.parse.quote(", ".join(artists or []))
		titlestring = urllib.parse.quote(title or "")
		response = requests.get(
			self.metadata["trackurl"].format(artist=artiststring,title=titlestring),
			headers=self._auth_headers()
		)
		data = response.json()
		imgurl = self.metadata_parse_response_track(data)
		if imgurl is not None: imgurl = self.postprocess_url(imgurl)
		if not self.validate_image_url(imgurl):
			return None
		return imgurl

	def get_image_artist(self,artist):
		artiststring = urllib.parse.quote(artist or "")
		response = requests.get(
			self.metadata["artisturl"].format(artist=artiststring),
			headers=self._auth_headers()
		)
		data = response.json()
		imgurl = self.metadata_parse_response_artist(data)
		if imgurl is not None: imgurl = self.postprocess_url(imgurl)
		if not self.validate_image_url(imgurl):
			return None
		return imgurl

	def get_image_album(self,album):
		artists, title = album
		artiststring = urllib.parse.quote(", ".join(artists or []))
		titlestring = urllib.parse.quote(title or "")
		response = requests.get(
			self.metadata["albumurl"].format(artist=artiststring,title=titlestring),
			headers=self._auth_headers()
		)
		data = response.json()
		imgurl = self.metadata_parse_response_album(data)
		if imgurl is not None: imgurl = self.postprocess_url(imgurl)
		if not self.validate_image_url(imgurl):
			return None
		return imgurl

	def handle_json_result_error(self,result):
		if not isinstance(result, dict):
			return True
		res = result.get('tracks') or result.get('albums') or result.get('artists') or {}
		if not isinstance(res, dict) or not res.get('items'):
			return True