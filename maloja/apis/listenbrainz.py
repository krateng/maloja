from ._base import APIHandler
from ._exceptions import *
from .. import database
import datetime

from doreah.settings import get_settings


class Listenbrainz(APIHandler):
	__apiname__ = "Listenbrainz"
	__doclink__ = "https://listenbrainz.readthedocs.io/en/production/"
	__aliases__ = [
		"listenbrainz/1",
		"lbrnz/1"
	]

	def init(self):
		self.methods = {
			"submit-listens":self.submit,
			"validate-token":self.validate_token
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
			token = self.get_token_from_request_keys(keys)
		except:
			raise BadAuthException()

		if token not in database.allAPIkeys():
			raise InvalidAuthException()

		try:
			listentype = keys["listen_type"]
			payload = keys["payload"]
		except:
			raise MalformedJSONException()

		if listentype == "playing_now":
			return 200,{"status":"ok"}
		elif listentype in ["single","import"]:
			for listen in payload:
				try:
					metadata = listen["track_metadata"]
					artiststr, titlestr = metadata["artist_name"], metadata["track_name"]
					try:
						timestamp = int(listen["listened_at"])
					except:
						timestamp = None
				except:
					raise MalformedJSONException()

				self.scrobble(artiststr,titlestr,timestamp)

			return 200,{"status":"ok"}


	def validate_token(self,pathnodes,keys):
		try:
			token = self.get_token_from_request_keys(keys)
		except:
			raise BadAuthException()
		if token not in database.allAPIkeys():
			raise InvalidAuthException()
		else:
			return 200,{"code":200,"message":"Token valid.","valid":True,"user_name":get_settings("NAME") or 'Maloja User'}

	def get_token_from_request_keys(self,keys):
		if 'token' in keys:
			return keys.get("token").strip()
		if 'Authorization' in keys:
			auth = keys.get("Authorization")
			if auth.startswith('token '):
				return auth.replace("token ","",1).strip()
			if auth.startswith('Token '):
				return auth.replace("Token ","",1).strip()
		raise BadAuthException()
