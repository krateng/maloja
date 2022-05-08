from ._base import APIHandler
from ._exceptions import *
from .. import database
from ._apikeys import apikeystore

from bottle import request

class AudioscrobblerLegacy(APIHandler):
	__apiname__ = "Legacy Audioscrobbler"
	__doclink__ = "https://web.archive.org/web/20190531021725/https://www.last.fm/api/submissions"
	__aliases__ = [
		"audioscrobbler_legacy",
		"audioscrobbler/1.2"
	]

	def init(self):

		# no need to save these on disk, clients can always request a new session
		self.mobile_sessions = {}
		self.methods = {
			"handshake":self.handshake,
			"nowplaying":self.now_playing,
			"scrobble":self.submit_scrobble
		}
		self.errors = {
			BadAuthException:(403,"BADAUTH\n"),
			InvalidAuthException:(403,"BADAUTH\n"),
			InvalidMethodException:(400,"FAILED\n"),
			InvalidSessionKey:(403,"BADSESSION\n"),
			ScrobblingException:(500,"FAILED\n")
		}

	def get_method(self,pathnodes,keys):
		if keys.get("hs") == 'true': return 'handshake'
		else: return pathnodes[0]

	def handshake(self,pathnodes,keys):
		auth = keys.get("a")
		timestamp = keys.get("t")
		apikey = keys.get("api_key")
		host = keys.get("Host")
		protocol = 'http' if (keys.get("u") == 'nossl') else request.urlparts.scheme

		if auth is not None:
			for client in apikeystore:
				key = apikeystore[client]
				if self.check_token(auth,key,timestamp):
					sessionkey = self.generate_key(client)
					return 200, (
						"OK\n"
						f"{sessionkey}\n"
						f"{protocol}://{host}/apis/audioscrobbler_legacy/nowplaying\n"
						f"{protocol}://{host}/apis/audioscrobbler_legacy/scrobble\n"
						)
			else:
				raise InvalidAuthException()
		else:
			raise BadAuthException()

	def now_playing(self,pathnodes,keys):
		# I see no implementation in the other compatible APIs, so I have just
		# created a route that always says it was successful except if the
		# session is invalid
		if keys.get("s") is None or keys.get("s") not in self.mobile_sessions:
			raise InvalidSessionKey()
		else:
			return 200,"OK\n"

	def submit_scrobble(self,pathnodes,keys):
		key = keys.get("s")
		if key is None or key not in self.mobile_sessions:
			raise InvalidSessionKey()
		client = self.mobile_sessions.get(key)
		for count in range(50):
			artist_key = f"a[{count}]"
			album_key = f"b[{count}]"
			length_key = f"l[{count}]"
			track_key = f"t[{count}]"
			time_key = f"i[{count}]"
			if artist_key not in keys or track_key not in keys:
				return 200,"OK\n"
			artiststr,titlestr = keys[artist_key], keys[track_key]
			try:
				timestamp = int(keys[time_key])
			except Exception:
				timestamp = None

			scrobble = {
				'track_artists':[artiststr],
				'track_title':titlestr,
				'scrobble_time':timestamp,
			}
			if album_key in keys:
				scrobble['album_name'] = keys[album_key]
			if length_key in keys:
				scrobble['track_length'] = keys[length_key]

			#database.createScrobble(artists,title,timestamp)
			self.scrobble(scrobble, client=client)
		return 200,"OK\n"


	def check_token(self, received_token, expected_key, ts):
		expected_token = md5(md5(expected_key) + ts)
		return received_token == expected_token

	def generate_key(self,client):
		key = "".join(
		    str(
		        random.choice(
		            list(range(10)) + list("abcdefghijklmnopqrstuvwxyz") +
		            list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))) for _ in range(64))

		self.mobile_sessions[key] = client
		return key


import hashlib
import random

def md5(input):
	m = hashlib.md5()
	m.update(bytes(input,encoding="utf-8"))
	return m.hexdigest()
