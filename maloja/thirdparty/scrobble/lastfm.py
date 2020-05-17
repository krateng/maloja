from . import ScrobbleInterface

from doreah.settings import get_settings

class LastFMScrobbler(ScrobbleInterface,LastFMInterface):

	scrobbleurl = "http://ws.audioscrobbler.com/2.0/"
	required_settings = [
		"LASTFM_API_KEY",
		"LASTFM_API_SK",
		"LASTFM_API_SECRET"
	]
	activated_setting = "SCROBBLE_LASTFM"

	def parse_response(self,data):
		return data.attrib.get("status") == "ok" and data.find("scrobbles").attrib.get("ignored") == "0"

	def postdata(self,artists,title,timestamp):
		return self.query_compose({
			"method":"track.scrobble",
			"artist[0]":", ".join(artists),
			"track[0]":title,
			"timestamp":timestamp,
			"api_key":get_settings("LASTFM_API_KEY"),
			"sk":get_settings("LASTFM_API_SK")
		})
