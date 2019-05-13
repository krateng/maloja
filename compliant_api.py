from doreah.logging import log
import hashlib
import random
import database
import datetime
from cleanup import CleanerAgent
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



def handle(path,keys,headers,auth):
	print("API request: " + str(path))
	print("Keys:")
	for k in keys:
		print("\t" + str(k) + ": " + str(keys.get(k)))
	print("Headers:")
	for h in headers:
		print("\t" + str(h) + ": " + str(headers.get(h)))
	print("Auth: " + str(auth))

	try:
		if path[0] in ["audioscrobbler","gnukebox","gnufm"]:
			response = handle_audioscrobbler(path[1:],keys)
		elif path[0] in ["listenbrainz","lbrnz"]:
			response = handle_listenbrainz(path[1:],keys,headers)
		else:
			response = {"error_message":"Invalid scrobble protocol"}
	except:
		response = {"error_message":"Unknown API error"}
		raise

	print("Response: " + str(response))
	return response

# no need to save these on disk, clients can always request a new session
mobile_sessions = []

def handle_audioscrobbler(path,keys):

	if path[0] == "2.0":

		if keys.get("method") == "auth.getMobileSession":
			token = keys.get("authToken")
			user = keys.get("username")
			password = keys.get("password")
			# either username and password
			if user is not None and password is not None:
				if password in database.allAPIkeys():
					sessionkey = generate_key(mobile_sessions)
					return {"session":{"key":sessionkey}}
			# or username and token (deprecated by lastfm)
			elif user is not None and token is not None:
				for key in database.allAPIkeys():
					if md5(user + md5(key)) == token:
						sessionkey = generate_key(mobile_sessions)
						return {"session":{"key":sessionkey}}
			return {"error":4}


		elif keys.get("method") == "track.scrobble":
			if keys.get("sk") is None or keys.get("sk") not in mobile_sessions:
				return {"error":9}
			else:

				if "track" in keys and "artist" in keys:
					artiststr,titlestr = keys["artist"], keys["track"]
					(artists,title) = cla.fullclean(artiststr,titlestr)
					timestamp = int(keys["timestamp"])
					database.createScrobble(artists,title,timestamp)
					return {"scrobbles":{"@attr":{"ignored":0}}}
				else:
					for num in range(50):
						if "track[" + str(num) + "]" in keys:
							artiststr,titlestr = keys["artist[" + str(num) + "]"], keys["track[" + str(num) + "]"]
							(artists,title) = cla.fullclean(artiststr,titlestr)
							timestamp = int(keys["timestamp[" + str(num) + "]"])
							database.createScrobble(artists,title,timestamp)
					return {"scrobbles":{"@attr":{"ignored":0}}}

		return {"error":3}

	else:
		return {"error_message":"API version not supported"}


def handle_listenbrainz(path,keys,headers):

	if path[0] == "1":

		if path[1] == "submit-listens":

			if headers.get("Authorization") is not None:
				token = headers.get("Authorization").replace("token ","").strip()
				if token in database.allAPIkeys():
					if "payload" in keys:
						if keys["listen_type"] in ["single","import"]:
							for listen in keys["payload"]:
								metadata = listen["track_metadata"]
								artiststr, titlestr = metadata["artist_name"], metadata["track_name"]
								(artists,title) = cla.fullclean(artiststr,titlestr)
								try:
									timestamp = int(listen["listened_at"])
								except:
									timestamp = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp())
								database.createScrobble(artists,title,timestamp)
						return {"code":200,"status":"ok"}
					else:
						response.status = 400
						return {"code":400,"error":"Invalid JSON document submitted."}


				else:
					return {"error":"Bad Auth"}

			else:
				return {"code":401,"error":"You need to provide an Authorization header."}

		else:
			return {"error_message":"Invalid API method"}
	else:
		return {"error_message":"API version not supported"}
