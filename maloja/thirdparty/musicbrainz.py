from . import MetadataInterface, utf, b64
import hashlib
import urllib.parse, urllib.request
import json
import time
import threading
from ..__pkginfo__ import versionstr, author, links

class MusicBrainz(MetadataInterface):
	name = "MusicBrainz"
	identifier = "musicbrainz"

	# musicbrainz is rate-limited
	lock = threading.Lock()
	useragent = "Maloja/" + versionstr + " ( https://github.com/" + author["github"] + "/" + links["github"] + " )"

	settings = {
	}

	metadata = {
		"response_type":"json",
		"response_parse_tree_track": ["images",0,"image"],
		"required_settings": [],
		"activated_setting": "METADATA_MUSICBRAINZ"
	}

	def get_image_artist(self,artist):
		return None
		# not supported


	def get_image_track(self,track):
		self.lock.acquire()
		try:
			artists, title = track
			artiststring = ", ".join(artists) #Join artists collection into string
			titlestring = title
			querystr = urllib.parse.urlencode({
				"fmt":"json",
				"query":"{title} {artist}".format(artist=artiststring,title=titlestring)
			})
			req = urllib.request.Request(**{
				"url":"https://musicbrainz.org/ws/2/release?" + querystr,
				"method":"GET",
				"headers":{
					"User-Agent":self.useragent
				}
			})
			response = urllib.request.urlopen(req)
			responsedata = response.read()
			data = json.loads(responsedata)
			mbid = data["releases"][0]["id"]
			response = urllib.request.urlopen(
				"https://coverartarchive.org/release/{mbid}?fmt=json".format(mbid=mbid)
			)
			responsedata = response.read()
			data = json.loads(responsedata)
			imgurl = self.metadata_parse_response_track(data)
			if imgurl is not None: imgurl = self.postprocess_url(imgurl)
			return imgurl

		except:
			return None
		finally:
			time.sleep(2)
			self.lock.release()
