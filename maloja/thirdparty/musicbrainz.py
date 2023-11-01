from . import MetadataInterface
import urllib.parse, urllib.request
import json
import time
import threading
from ..__pkginfo__ import USER_AGENT

class MusicBrainz(MetadataInterface):
	name = "MusicBrainz"
	identifier = "musicbrainz"

	# musicbrainz is rate-limited
	lock = threading.Lock()
	useragent = USER_AGENT

	settings = {
	}

	metadata = {
		"response_type":"json",
		"response_parse_tree_track": ["images",0,"thumbnails","500"],
		"required_settings": [],
	}

	def get_image_artist(self,artist):
		return None
		# not supported

	def get_image_album(self,album):
		return None

	def get_image_track(self,track):
		self.lock.acquire()
		try:
			artists, title = track
			searchstr = f'recording:"{title}"'
			for artist in artists:
				searchstr += f' artist:"{artist}"'
			querystr = urllib.parse.urlencode({
				"fmt":"json",
				"query":searchstr
			})
			req = urllib.request.Request(**{
				"url":"https://musicbrainz.org/ws/2/recording?" + querystr,
				"method":"GET",
				"headers":{
					"User-Agent":self.useragent
				}
			})
			response = urllib.request.urlopen(req)
			responsedata = response.read()
			data = json.loads(responsedata)
			entity = data["recordings"][0]["releases"][0]
			coverartendpoint = "release"
			while True:
				mbid = entity["id"]
				try:
					response = urllib.request.urlopen(
						f"https://coverartarchive.org/{coverartendpoint}/{mbid}?fmt=json"
					)
					responsedata = response.read()
					data = json.loads(responsedata)
					imgurl = self.metadata_parse_response_track(data)
				except:
					imgurl = None
				if imgurl is None:
					entity = entity["release-group"]
					# this will raise an error so we don't stay in the while loop forever
					coverartendpoint = "release-group"
					continue

				imgurl = self.postprocess_url(imgurl)
				return imgurl

		except Exception:
			return None
		finally:
			time.sleep(2)
			self.lock.release()
