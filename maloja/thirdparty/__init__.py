# these different interfaces are for the different roles a third party service
# can fulfill. implementing them adds some generic functionality to attempt to
# actually perform the role, but this will have to be overwritten in most cases.
# functionality is separated into different layers to allow partial override

# also yes, we're using singleton classes for the different providers
# pls don't sue me

import xml.etree.ElementTree as ElementTree
import urllib.parse, urllib.request
from doreah.settings import get_settings
from doreah.logging import log




services = {
	"proxyscrobble":[],
	"import":[],
	"metadata":[]
}


def proxy_scrobble_all(artists,title,timestamp):
	for service in services["proxyscrobble"]:
		service.scrobble(artists,title,timestamp)




class GenericInterface:
	def active_proxyscrobble(self):
		return False
	def active_import(self):
		return False
	def active_metadata(self):
		return False

	settings = {}

	proxyscrobble = {}
	scrobbleimport = {}
	metadata = {}

	def __init__(self):
		# populate from settings file once on creation
		# avoid constant disk access, restart on adding services is acceptable
		for key in self.settings:
			self.settings[key] = get_settings(self.settings[key])

	def __init_subclass__(cls,abstract=False):
		if not abstract:
			s = cls()
			if s.active_proxyscrobble():
				services["proxyscrobble"].append(s)
				log(cls.name + "Registered as proxy scrobble target")
			if s.active_import():
				services["import"].append(s)
				log(cls.name + "Registered as scrobble import source")
			if s.active_metadata():
				services["metadata"].append(s)
				log(cls.name + "Registered for metadata provider")

# proxy scrobbler
class ProxyScrobbleInterface(GenericInterface,abstract=True):

	proxyscrobble = {
		"required_settings":[],
		"activated_setting":None
	}

	def active_proxyscrobble(self):
		return (
			all(self.settings[key] not in [None,"ASK"] for key in self.proxyscrobble["required_settings"]) and
			get_settings(self.proxyscrobble["activated_setting"])
		)

	def scrobble(self,artists,title,timestamp):
		response = urllib.request.urlopen(
			self.proxyscrobble["scrobbleurl"],
			data=utf(self.postdata(artists,title,timestamp)))
		responsedata = response.read()
		if self.proxyscrobble["response_type"] == "xml":
			data = ElementTree.fromstring(responsedata)
			return self.parse_response(data)

# scrobble import
class ImportInterface(GenericInterface,abstract=True):

	scrobbleimport = {
		"required_settings":[],
		"activated_setting":None
	}

	def active_import(self):
		return (
			all(self.settings[key] not in [None,"ASK"] for key in self.scrobbleimport["required_settings"]) and
			get_settings(self.scrobbleimport["activated_setting"])
		)


# metadata
class MetadataInterface(GenericInterface,abstract=True):

	metadata = {
		"required_settings":[],
		"activated_setting":None
	}

	def active_metadata(self):
		return (
			all(self.settings[key] not in [None,"ASK"] for key in self.metadata["required_settings"]) and
			get_settings(self.metadata["activated_setting"])
		)





### useful stuff

def utf(st):
	return st.encode(encoding="UTF-8")




### actually create everything

from . import lastfm
