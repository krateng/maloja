from ._base import APIHandler
from ._exceptions import *
from .. import database
import datetime
from ._apikeys import apikeystore
from ..database.exceptions import DuplicateScrobble, DuplicateTimestamp

from ..pkg_global.conf import malojaconfig


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
			BadAuthException: (401, {"code": 401, "error": "You need to provide an Authorization header."}),
			InvalidAuthException: (401, {"code": 401, "error": "Incorrect Authorization"}),
			InvalidMethodException: (200, {"code": 200, "error": "Invalid Method"}),
			MalformedJSONException: (400, {"code": 400, "error": "Invalid JSON document submitted."}),
			DuplicateScrobble: (200, {"status": "ok"}),
			DuplicateTimestamp: (409, {"error": "Scrobble with the same timestamp already exists."}),
			Exception: (500, {"code": 500, "error": "Unspecified server error."})
		}

	def get_method(self,pathnodes,keys):
		return pathnodes.pop(0)

	def submit(self,pathnodes,keys):
		try:
			token = self.get_token_from_request_keys(keys)
		except Exception:
			raise BadAuthException()

		client = apikeystore.check_and_identify_key(token)

		if not client:
			raise InvalidAuthException()

		try:
			listentype = keys["listen_type"]
			payload = keys["payload"]
		except Exception:
			raise MalformedJSONException()

		if listentype == "playing_now":
			return 200,{"status":"ok"}
		elif listentype in ["single","import"]:
			for listen in payload:
				try:
					metadata = listen["track_metadata"]
					artiststr, titlestr = metadata["artist_name"], metadata["track_name"]
					albumstr = metadata.get("release_name")
					additional = metadata.get("additional_info",{})
					try:
						timestamp = int(listen["listened_at"])
					except Exception:
						timestamp = None
				except Exception:
					raise MalformedJSONException()

				extrafields = {
					# fields that will not be consumed by regular scrobbling
					# will go into 'extra'
					k:additional[k]
					for k in ['track_mbid', 'release_mbid', 'artist_mbids','recording_mbid','tags']
					if k in additional
				}

				self.scrobble({
					'track_artists':[artiststr],
					'track_title':titlestr,
					'album_title':albumstr,
					'scrobble_time':timestamp,
					'scrobble_duration': int(additional.get("duration_ms") / 1000) if additional.get("duration_ms") else additional.get("duration"),
					**extrafields
				},client=client)

			return 200,{"status":"ok"}


	def validate_token(self,pathnodes,keys):
		try:
			token = self.get_token_from_request_keys(keys)
		except Exception:
			raise BadAuthException()
		if not apikeystore.check_key(token):
			raise InvalidAuthException()
		else:
			return 200,{"code":200,"message":"Token valid.","valid":True,"user_name":malojaconfig["NAME"]}

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
