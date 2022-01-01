from . import ProxyScrobbleInterface, ImportInterface
import urllib.request
from doreah.logging import log
import json


class OtherMalojaInstance(ProxyScrobbleInterface, ImportInterface):

	name = "Maloja"
	identifier = "maloja"

	settings = {
		"apikey":"OTHER_MALOJA_API_KEY",
		"instance":"OTHER_MALOJA_URL"
	}

	proxyscrobble = {
		"scrobbleurl": "http://ws.audioscrobbler.com/2.0/",
		"required_settings": ["apikey","instance"],
		"activated_setting": "FORWARD_OTHER_MALOJA_SERVER"
	}

	scrobbleimport = {
		"required_settings":["apikey","instance"]
	}



	def active_proxyscrobble(self):
		return False

	def get_remote_scrobbles(self):
		url = f"{self.settings['instance']}/apis/mlj_1/scrobbles"

		response = urllib.request.urlopen(url)
		data = json.loads(response.read().decode('utf-8'))

		for scrobble in data['list']:
			yield scrobble
		return True
