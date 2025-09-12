from ._base import APIHandler
from ._exceptions import *
from .. import database
import datetime
from ._apikeys import apikeystore
from ..database.exceptions import DuplicateScrobble, DuplicateTimestamp
from ..malojatime import MTRangeComposite, MTRangeGregorian, today, thisweek, thismonth, thisyear, alltime
from ..malojauri import compose_querystring, internal_to_uri

from ..images import get_album_image
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
			"validate-token":self.validate_token,
			"art":self.art
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
					'track_length': additional.get("duration"),
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

	def art(self,pathnodes,keys):
		timeranges = {
			'this_week': thisweek(),
			'this_month': thismonth(),
			'this_year': thisyear(),
			'week': MTRangeComposite(since=today().next(-7),to=today()),
			'month': MTRangeComposite(since=MTRangeGregorian(today().year, thismonth().next(-1).month, today().day),to=today()),
			'quarter': MTRangeComposite(since=MTRangeGregorian(today().year, thismonth().next(-3).month, today().day),to=today()),
			'year':  MTRangeComposite(since=MTRangeGregorian(thisyear().next(-1).year, today().month, today().day),to=today()),
			'half_yearly': MTRangeComposite(since=MTRangeGregorian(today().year, thismonth().next(-6).month, today().day),to=today()),
			'all_time': alltime()
		}
		timeranges_english = {
			"this_week": "this week",
			"this_month": "this month",
			"this_year": "this year",
			"week": "last week",
			"month": "last month",
			"quarter": "last quarter",
			"year": "last year",
			"half_yearly": "last 6 months",
			"all_time": "of all time"
		}
		svg_template = """<svg version="1.1"
	xmlns="http://www.w3.org/2000/svg"
	xmlns:xlink="http://www.w3.org/1999/xlink"
	role="img"
	viewBox="0 0 {width} {height}"
	width="{width}"
	height="{height}">
<title>Top {amount} Releases {time_range} for {user_name}</title>
<desc>{description}</desc>

<rect id="background" fill="#FFFFFF" x="0" ry="0" width="{width}" height="{height}"/>
	{images}
</svg>
"""
		image_template = """<a href="{item_url}"> target="_blank">
<image
        x="{x}"
        y="{y}"
        width="{width}"
        height="{height}"
        preserveAspectRatio="xMidYMid slice"
        href="{image_url}">
        <title>{title} - {artist}</title>
</image>
</a>
"""
		
		if self.get_method(pathnodes, keys) == "grid-stats":
			try:
				"""
				Confirm that all of the parameters are within values supported by the actual ListenBrainz API.
				pathnodes values are also set as human-readable variables, for later!
				"""
				checks = [
					((user_name := pathnodes[0]) == malojaconfig["NAME"]), # Because there's only one user, and thus any other input would fail
					((time_range := pathnodes[1]) in timeranges),
					(1 <= (dimension := int(pathnodes[2])) <= 5),
					(int(layout := pathnodes[3]) == 0),
					(128 <= (image_size := int(pathnodes[4])) <= 1024)
				]
			except:
				raise MalformedJSONException()
			if not all(checks):
				raise MalformedJSONException()
			tile_size = image_size // dimension
			albums = database.get_charts_albums(timerange=timeranges[time_range])[0:dimension**2]
			# Fetches the necessary top albums for the given time range.
			# This implementation only does square grids at the moment, so all we need to do is get our dimension to the second power
			description = ""
			images = ""
			for i in range(len(albums)):
				title = albums[i]['album']['albumtitle']
				firstartist = albums[i]['album']['artists'][0]
				description += f"{i+1}. {title} - {firstartist} \n"
				images += image_template.format(
					item_url = "/album?" + compose_querystring(internal_to_uri(albums[i])),
					image_url = get_album_image(album_id=albums[i]['album_id']),
					x = (i // dimension) * tile_size,
					y = (i % dimension) * tile_size,
					width = tile_size,
					height = tile_size,
					title = title,
					artist = firstartist
				)
			return 200,svg_template.format(
				width = image_size,
				height = image_size,
				amount = dimension**2,
				time_range = timeranges_english[time_range],
				user_name = user_name,
				description = description,
				images = images
			)
			# return 200,albums
			


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
