import requests

class MalojaInstance:
	def __init__(self,base_url,key):
		self.base_url = base_url
		self.key = key

	def test(self):
		url = self.base_url + '/apis/mlj_1/test'
		response = requests.get(url,{'key':self.key})

		return (response.status_code == 200)

	def scrobble(self,artists,title,timestamp=None,album=None,duration=None):
		payload = {
            'key':self.key,
			'artists':artists,
			'title':title,
			'time':timestamp,
			'album':album,
			'duration':duration
		}

		url = self.base_url + '/apis/mlj_1/newscrobble'
		response = requests.post(url,payload)

		return response.json()
