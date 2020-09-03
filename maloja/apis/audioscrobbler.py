from ._base import APIHandler
from ._exceptions import *
from .. import database

class Audioscrobbler(APIHandler):
	__apiname__ = "Audioscrobbler"
	__doclink__ = "https://www.last.fm/api/scrobbling"
	__aliases__ = [
		"audioscrobbler/2.0",
		"gnufm/2.0",
		"gnukebox/2.0",
	]

	def init(self):

		# no need to save these on disk, clients can always request a new session
		self.mobile_sessions = []
		self.methods = {
			"auth.getMobileSession":self.authmobile,
			"track.scrobble":self.submit_scrobble
		}
		self.errors = {
			BadAuthException:(400,{"error":6,"message":"Requires authentication"}),
			InvalidAuthException:(401,{"error":4,"message":"Invalid credentials"}),
			InvalidMethodException:(200,{"error":3,"message":"Invalid method"}),
			InvalidSessionKey:(403,{"error":9,"message":"Invalid session key"}),
			ScrobblingException:(500,{"error":8,"message":"Operation failed"})
		}

	def get_method(self,pathnodes,keys):
		return keys.get("method")

	def authmobile(self,pathnodes,keys):
		token = keys.get("authToken")
		user = keys.get("username")
		password = keys.get("password")
		# either username and password
		if user is not None and password is not None:
			if password in database.allAPIkeys():
				sessionkey = generate_key(self.mobile_sessions)
				return 200,{"session":{"key":sessionkey}}
			else:
				raise InvalidAuthException()
		# or username and token (deprecated by lastfm)
		elif user is not None and token is not None:
			for key in database.allAPIkeys():
				if md5(user + md5(key)) == token:
					sessionkey = generate_key(self.mobile_sessions)
					return 200,{"session":{"key":sessionkey}}
			raise InvalidAuthException()
		else:
			raise BadAuthException()

	def submit_scrobble(self,pathnodes,keys):
		if keys.get("sk") is None or keys.get("sk") not in self.mobile_sessions:
			raise InvalidSessionKey()
		else:
			if "track" in keys and "artist" in keys:
				artiststr,titlestr = keys["artist"], keys["track"]
				#(artists,title) = cla.fullclean(artiststr,titlestr)
				try:
					timestamp = int(keys["timestamp"])
				except:
					timestamp = None
				#database.createScrobble(artists,title,timestamp)
				self.scrobble(artiststr,titlestr,time=timestamp)
				return 200,{"scrobbles":{"@attr":{"ignored":0}}}
			else:
				for num in range(50):
					if "track[" + str(num) + "]" in keys:
						artiststr,titlestr = keys["artist[" + str(num) + "]"], keys["track[" + str(num) + "]"]
						#(artists,title) = cla.fullclean(artiststr,titlestr)
						timestamp = int(keys["timestamp[" + str(num) + "]"])
						#database.createScrobble(artists,title,timestamp)
						self.scrobble(artiststr,titlestr,time=timestamp)
				return 200,{"scrobbles":{"@attr":{"ignored":0}}}


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
