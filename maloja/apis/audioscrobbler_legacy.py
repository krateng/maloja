from ._base import APIHandler
from ._exceptions import *
from .. import database

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
		self.mobile_sessions = []
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
		protocol = request.urlparts.scheme
		if (keys.get("u") == 'nossl'): protocol = 'http' #user override

		if auth is not None:
			for key in database.allAPIkeys():
				if check_token(auth, key, timestamp):
					sessionkey = generate_key(self.mobile_sessions)
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
		if keys.get("s") is None or keys.get("s") not in self.mobile_sessions:
			raise InvalidSessionKey()
		else:
			for count in range(0,50):
				artist_key = f"a[{count}]"
				track_key = f"t[{count}]"
				time_key = f"i[{count}]"
				if artist_key in keys and track_key in keys:
					artiststr,titlestr = keys[artist_key], keys[track_key]
					try:
						timestamp = int(keys[time_key])
					except:
						timestamp = None
					#database.createScrobble(artists,title,timestamp)
					self.scrobble(artiststr,titlestr,time=timestamp)
				else:
					return 200,"OK\n"
			return 200,"OK\n"


import hashlib
import random

def md5(input):
	m = hashlib.md5()
	m.update(bytes(input,encoding="utf-8"))
	return m.hexdigest()

def generate_key(ls):
	key = ""
	for i in range(64):
		key += str(random.choice(list(range(10)) + list("abcdefghijklmnopqrstuvwxyz") + list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")))
	ls.append(key)
	return key

def lastfm_token(password, ts):
	return md5(md5(password) + ts)

def check_token(received_token, expected_key, ts):
	expected_token = lastfm_token(expected_key, ts)
	return received_token == expected_token
