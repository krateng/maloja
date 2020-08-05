from doreah.logging import log
import hashlib
import random
from . import database
import datetime
import itertools
import sys
from .cleanup import CleanerAgent
from bottle import response

## GNU-FM-compliant scrobbling


cla = CleanerAgent()

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

#def check_sig(keys):
#	try:
#		sig = keys.pop("api_sig")
#		text = "".join([key + keys[key] for key in sorted(keys.keys())]) + # secret
#		assert sig == md5(text)
#		return True
#	except:
#		return False


handlers = {}

def handler(apiname,version):
	def deco(cls):
		handlers[(apiname,version)] = cls()
		return cls
	return deco

def handle(path,keys):
	log("API request: " + str(path))# + " | Keys: " + str({k:keys.get(k) for k in keys}))

	if len(path)>1 and (path[0],path[1]) in handlers:
		handler = handlers[(path[0],path[1])]
		path = path[2:]
		try:
			response.status,result = handler.handle(path,keys)
		except:
			type = sys.exc_info()[0]
			response.status,result = handler.errors[type]
	else:
		result = {"error":"Invalid scrobble protocol"}
		response.status = 500


	log("Response: " + str(result))
	return result

def scrobbletrack(artiststr,titlestr,timestamp):
	try:
		log("Incoming scrobble (compliant API): ARTISTS: " + artiststr + ", TRACK: " + titlestr,module="debug")
		(artists,title) = cla.fullclean(artiststr,titlestr)
		database.createScrobble(artists,title,timestamp)
		database.sync()
	except:
		raise ScrobblingException()


class BadAuthException(Exception): pass
class InvalidAuthException(Exception): pass
class InvalidMethodException(Exception): pass
class InvalidSessionKey(Exception): pass
class MalformedJSONException(Exception): pass
class ScrobblingException(Exception): pass

class APIHandler:
	# make these classes singletons
	_instance = None
	def __new__(cls, *args, **kwargs):
		if not isinstance(cls._instance, cls):
			cls._instance = object.__new__(cls, *args, **kwargs)
		return cls._instance


	def handle(self,pathnodes,keys):
		try:
			methodname = self.get_method(pathnodes,keys)
			method = self.methods[methodname]
		except:
			raise InvalidMethodException()
		return method(pathnodes,keys)

@handler("audioscrobbler","2.0")
@handler("gnufm","2.0")
@handler("gnukebox","2.0")
class GNUFM2(APIHandler):
	def __init__(self):
		# no need to save these on disk, clients can always request a new session
		self.mobile_sessions = []
		self.methods = {
			"auth.getMobileSession":self.authmobile,
			"track.scrobble":self.scrobble
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

	def scrobble(self,pathnodes,keys):
		if keys.get("sk") is None or keys.get("sk") not in self.mobile_sessions:
			raise InvalidSessionKey()
		else:
			if "track" in keys and "artist" in keys:
				artiststr,titlestr = keys["artist"], keys["track"]
				#(artists,title) = cla.fullclean(artiststr,titlestr)
				timestamp = int(keys["timestamp"])
				#database.createScrobble(artists,title,timestamp)
				scrobbletrack(artiststr,titlestr,timestamp)
				return 200,{"scrobbles":{"@attr":{"ignored":0}}}
			else:
				for num in range(50):
					if "track[" + str(num) + "]" in keys:
						artiststr,titlestr = keys["artist[" + str(num) + "]"], keys["track[" + str(num) + "]"]
						#(artists,title) = cla.fullclean(artiststr,titlestr)
						timestamp = int(keys["timestamp[" + str(num) + "]"])
						#database.createScrobble(artists,title,timestamp)
						scrobbletrack(artiststr,titlestr,timestamp)
				return 200,{"scrobbles":{"@attr":{"ignored":0}}}



@handler("listenbrainz","1")
@handler("lbrnz","1")
class LBrnz1(APIHandler):
	def __init__(self):
		self.methods = {
			"submit-listens":self.submit
		}
		self.errors = {
			BadAuthException:(401,{"code":401,"error":"You need to provide an Authorization header."}),
			InvalidAuthException:(401,{"code":401,"error":"Incorrect Authorization"}),
			InvalidMethodException:(200,{"code":200,"error":"Invalid Method"}),
			MalformedJSONException:(400,{"code":400,"error":"Invalid JSON document submitted."}),
			ScrobblingException:(500,{"code":500,"error":"Unspecified server error."})
		}

	def get_method(self,pathnodes,keys):
		return pathnodes.pop(0)

	def submit(self,pathnodes,keys):
		try:
			token = keys.get("Authorization").replace("token ","").replace("Token ","").strip()
		except:
			raise BadAuthException()

		if token not in database.allAPIkeys():
			raise InvalidAuthException()

		try:
			if keys["listen_type"] in ["single","import"]:
				payload = keys["payload"]
				for listen in payload:
					metadata = listen["track_metadata"]
					artiststr, titlestr = metadata["artist_name"], metadata["track_name"]
					#(artists,title) = cla.fullclean(artiststr,titlestr)
					try:
						timestamp = int(listen["listened_at"])
					except:
						timestamp = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp())
					#database.createScrobble(artists,title,timestamp)
					scrobbletrack(artiststr,titlestr,timestamp)
					return 200,{"code":200,"status":"ok"}
			else:
				return 200,{"code":200,"status":"ok"}
		except:
			raise MalformedJSONException()
