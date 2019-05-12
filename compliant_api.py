from doreah.logging import log
import hashlib
import random
import database
from cleanup import CleanerAgent

## GNU-FM-compliant scrobbling


cla = CleanerAgent()

def md5(input):
	m = hashlib.md5()
	m.update(bytes(input,encoding="utf-8"))
	return m.hexdigest()


#def check_sig(keys):
#	try:
#		sig = keys.pop("api_sig")
#		text = "".join([key + keys[key] for key in sorted(keys.keys())]) + # secret
#		assert sig == md5(text)
#		return True
#	except:
#		return False



def handle(path,keys):
#	log("API REQUEST")
#	log(str(path))
#	for k in keys:
#		log(str(k) + ": " + str(keys.getall(k)))

	if path[0] == "audioscrobbler":
		return handle_audioscrobbler(path[1:],keys)


# no need to save these on disk, clients can always request a new session
mobile_sessions = []

def handle_audioscrobbler(path,keys):

	if path[0] == "2.0":

		if keys.get("method") == "auth.getMobileSession":
			token = keys.get("authToken")
			user = keys.get("username")
			for key in database.allAPIkeys():
				if md5(user + md5(key)) == token:
					sessionkey = ""
					for i in range(64):
						sessionkey += str(random.choice(list(range(10)) + list("abcdefghijklmnopqrstuvwxyz") + list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")))
					mobile_sessions.append(sessionkey)
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
