from ._base import APIHandler
from ._exceptions import *
from .. import database

class AudioscrobblerLegacy(APIHandler):
	__apiname__ = "Legacy Audioscrobbler"
	__doclink__ = "https://web.archive.org/web/20190531021725/https://www.last.fm/api/submissions"
	__aliases__ = [
		"audioscrobbler/1.2",
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
			BadAuthException:(200,"BADAUTH"),
			InvalidAuthException:(200,"BADAUTH"),
			InvalidMethodException:(200,{"error":3,"message":"Invalid method"}),
			InvalidSessionKey:(200,"BADSESSION"),
			ScrobblingException:(500,{"error":8,"message":"Operation failed"})
		}

	def get_method(self,pathnodes,keys):
		return keys.get("method")

	def handshake(self,pathnodes,keys):
		user = keys.get("u")
		auth = keys.get("a")
		timestamp = keys.get("t")
		apikey = keys.get("api_key")
		host = keys.get("Host")
		# expect username and password
		if user is not None and apikey is None:
			receivedToken = lastfmToken(password, timestamp)
			authenticated = False
			for key in database.allAPIkeys():
				if checkPassword(receivedToken, key, timestamp):
					authenticated = True
					break
			if authenticated:
				sessionkey = generate_key(self.mobile_sessions)
				return 200, "OK\n" +
					sessionkey + "\n" +
					protocol + "://"+domain+":"+port+"/apis/legacyaudioscrobbler/nowplaying" + "\n" +
					protocol + "://"+domain+":"+port+"/apis/legacyaudioscrobbler/scrobble" + "\n"
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
			return "OK"

	def submit_scrobble(self,pathnodes,keys):
		if keys.get("s") is None or keys.get("s") not in self.mobile_sessions:
			raise InvalidSessionKey()
		else:
			iterating = True
			count = 0
			while iterating:
				t = "t"+str(count) # track
				a = "a"+str(count) # artist
				i = "i"+str(count) # timestamp
				if t in keys and a in keys:
					artiststr,titlestr = keys[a], keys[t]
					#(artists,title) = cla.fullclean(artiststr,titlestr)
					try:
						timestamp = int(keys[i])
					except:
						timestamp = None
					#database.createScrobble(artists,title,timestamp)
					self.scrobble(artiststr,titlestr,time=timestamp)
					count += 1
				else:
					iterating = False
					return 200,"OK"


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

def lastfmToken(password, ts):
	return md5(md5(password), ts)

def checkPassword(receivedToken, expectedKey, ts):
	expectedToken = lastfmToken(expectedKey, ts)
	return receivedToken == expectedToken
