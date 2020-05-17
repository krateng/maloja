import xml.etree.ElementTree as ElementTree
import urllib

class ScrobbleInterface:

	required_settings = []
	activated_setting = ""

	def active(self):
		return (
			all(get_settings(settingname) not in [None,"ASK"] for settingname in self.required_settings) and
			get_settings(self.activated_setting)
		)

	def scrobble(self,artists,title,timestamp):
		response = urllib.request.urlopen(self.scrobbleurl,data=self.postdata(artists,title,timestamp))
		responsedata = response.read()
		if self.response_type == "xml":
			data = ElementTree.fromstring(responsedata)
			return self.parse_response(data)
