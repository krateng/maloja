from . import MetadataInterface
import requests
import time
import threading

class MusicBrainz(MetadataInterface):
	name = "MusicBrainz"
	identifier = "musicbrainz"

	# musicbrainz is rate-limited
	lock = threading.Lock()


	thumbnailsize_order = ['500','large','1200','250','small']

	settings = {
	}

	metadata = {
		"response_type":"json",
		"required_settings": [],
		"enabled_entity_types": ["album","track"]
	}

	def get_image_artist(self,artist):
		return None
		# not supported

	def get_image_album(self,album):
		self.lock.acquire()
		try:
			artists, title = album
			searchstr = f'release:"{title}"'
			for artist in artists:
				searchstr += f' artist:"{artist}"'
			res = requests.get(**{
				"url":"https://musicbrainz.org/ws/2/release",
				"params":{
					"fmt":"json",
					"query":searchstr
				},
				"headers":{
					"User-Agent":self.useragent
				}
			})
			data = res.json()
			entity = data["releases"][0]
			coverartendpoint = "release"
			while True:
				mbid = entity["id"]
				try:
					response = requests.get(
						f"https://coverartarchive.org/{coverartendpoint}/{mbid}",
						params={
							"fmt":"json"
						},
						headers={
							"User-Agent":self.useragent
						}
					)
					data = response.json()
					thumbnails = data['images'][0]['thumbnails']
					for size in self.thumbnailsize_order:
						if thumbnails.get(size) is not None:
							imgurl = thumbnails.get(size)
							continue
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

	def get_image_track(self,track):
		self.lock.acquire()
		try:
			artists, title = track
			searchstr = f'recording:"{title}"'
			for artist in artists:
				searchstr += f' artist:"{artist}"'
			res = requests.get(**{
				"url":"https://musicbrainz.org/ws/2/recording",
				"params":{
					"fmt":"json",
					"query":searchstr
				},
				"headers":{
					"User-Agent":self.useragent
				}
			})
			data = res.json()
			entity = data["recordings"][0]["releases"][0]
			coverartendpoint = "release"
			while True:
				mbid = entity["id"]
				try:
					response = requests.get(
						f"https://coverartarchive.org/{coverartendpoint}/{mbid}",
						params={
							"fmt":"json"
						}
					)
					data = response.json()
					thumbnails = data['images'][0]['thumbnails']
					for size in self.thumbnailsize_order:
						if thumbnails.get(size) is not None:
							imgurl = thumbnails.get(size)
							continue
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
