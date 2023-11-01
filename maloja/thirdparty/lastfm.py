from . import MetadataInterface, ProxyScrobbleInterface, utf
import hashlib
import requests
import xml.etree.ElementTree as ElementTree
from doreah.logging import log

class LastFM(MetadataInterface, ProxyScrobbleInterface):
	name = "LastFM"
	identifier = "lastfm"

	settings = {
		"apikey":"LASTFM_API_KEY",
		"sk":"LASTFM_API_SK",
		"secret":"LASTFM_API_SECRET",
		"username":"LASTFM_USERNAME",
		"password":"LASTFM_PASSWORD"
	}

	proxyscrobble = {
		"scrobbleurl": "http://ws.audioscrobbler.com/2.0/",
		"response_type":"xml",
		"required_settings": ["apikey","sk","secret"],
		"activated_setting": "SCROBBLE_LASTFM"
	}
	metadata = {
		#"artisturl": "https://ws.audioscrobbler.com/2.0/?method=artist.getinfo&artist={artist}&api_key={apikey}&format=json"
		"trackurl": "https://ws.audioscrobbler.com/2.0/?method=track.getinfo&track={title}&artist={artist}&api_key={apikey}&format=json",
		"albumurl": "https://ws.audioscrobbler.com/2.0/?method=album.getinfo&api_key={apikey}&artist={artist}&album={title}&format=json",
		"response_type":"json",
		"response_parse_tree_track": ["track","album","image",-1,"#text"],
		# technically just the album artwork, but we use it for now
		#"response_parse_tree_artist": ["artist","image",-1,"#text"],
		"response_parse_tree_album": ["album","image",-1,"#text"],
		"required_settings": ["apikey"],
		"enabled_entity_types": ["track","album"]
	}

	def get_image_artist(self,artist):
		return None
		# lastfm still provides that endpoint with data,
		# but doesn't provide actual images


	def proxyscrobble_parse_response(self,data):
		return data.attrib.get("status") == "ok" and data.find("scrobbles").attrib.get("ignored") == "0"

	def proxyscrobble_postdata(self,artists,title,timestamp):
		return self.query_compose({
			"method":"track.scrobble",
			"artist[0]":", ".join(artists),
			"track[0]":title,
			"timestamp":timestamp,
			"api_key":self.settings["apikey"],
			"sk":self.settings["sk"]
		})

	def authorize(self):
		try:
			response = requests.post(
				url=self.proxyscrobble['scrobbleurl'],
				params=self.query_compose({
					"method":"auth.getMobileSession",
					"username":self.settings["username"],
					"password":self.settings["password"],
					"api_key":self.settings["apikey"]
				}),
				headers={
					"User-Agent":self.useragent
				}
			)

			data = ElementTree.fromstring(response.text)
			self.settings["sk"] = data.find("session").findtext("key")
		except Exception as e:
			log("Error while authenticating with LastFM: " + repr(e))


	# creates signature and returns full query
	def query_compose(self,parameters):
		m = hashlib.md5()
		keys = sorted(str(k) for k in parameters)
		m.update(utf("".join(str(k) + str(parameters[k]) for k in keys)))
		m.update(utf(self.settings["secret"]))
		sig = m.hexdigest()
		return {**parameters,"api_sig":sig}

	def handle_json_result_error(self,result):
		if "track" in result and not result.get("track").get('album',{}):
			return True

		if "error" in result and result.get("error") == 6:
			return True
