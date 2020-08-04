# these different interfaces are for the different roles a third party service
# can fulfill. implementing them adds some generic functionality to attempt to
# actually perform the role, but this will have to be overwritten in most cases.
# functionality is separated into different layers to allow partial override

# also yes, we're using singleton classes for the different providers
# pls don't sue me

import xml.etree.ElementTree as ElementTree
import json
import urllib.parse, urllib.request
import base64
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

def get_image_track_all(track):
	for service in services["metadata"]:
		res = service.get_image_track(track)
		if res is not None:
			log("Got track image for " + str(track) + " from " + service.name)
			return res
		else:
			log("Could not get track image for " + str(track) + " from " + service.name)
def get_image_artist_all(artist):
	for service in services["metadata"]:
		res = service.get_image_artist(artist)
		if res is not None:
			log("Got artist image for " + str(artist) + " from " + service.name)
			return res
		else:
			log("Could not get artist image for " + str(artist) + " from " + service.name)



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
		try: self.authorize()
		except: pass

	def __init_subclass__(cls,abstract=False):
		if not abstract:
			s = cls()
			if s.active_proxyscrobble():
				services["proxyscrobble"].append(s)
				log(cls.name + " registered as proxy scrobble target")
			if s.active_import():
				services["import"].append(s)
				log(cls.name + " registered as scrobble import source")
			if s.active_metadata():
				services["metadata"].append(s)
				log(cls.name + " registered as metadata provider")

	def authorize(self):
		return True
		# per default. no authorization is necessary

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
			data=utf(self.proxyscrobble_postdata(artists,title,timestamp)))
		responsedata = response.read()
		if self.proxyscrobble["response_type"] == "xml":
			data = ElementTree.fromstring(responsedata)
			return self.proxyscrobble_parse_response(data)

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
			self.identifier in get_settings("METADATA_PROVIDERS")
		)

	def get_image_track(self,track):
		artists, title = track
		artiststring = urllib.parse.quote(", ".join(artists))
		titlestring = urllib.parse.quote(title)
		response = urllib.request.urlopen(
			self.metadata["trackurl"].format(artist=artiststring,title=titlestring,**self.settings)
		)

		responsedata = response.read()
		if self.metadata["response_type"] == "json":
			data = json.loads(responsedata)
			return self.metadata_parse_response_track(data)

	def get_image_artist(self,artist):
		artiststring = urllib.parse.quote(artist)
		response = urllib.request.urlopen(
			self.metadata["artisturl"].format(artist=artiststring,**self.settings)
		)

		responsedata = response.read()
		if self.metadata["response_type"] == "json":
			data = json.loads(responsedata)
			return self.metadata_parse_response_artist(data)

	# default function to parse response by descending down nodes
	# override if more complicated
	def metadata_parse_response_artist(self,data):
		res = data
		for node in self.metadata["response_parse_tree_artist"]:
			try:
				res = res[node]
			except:
				return None
		return res

	def metadata_parse_response_track(self,data):
		res = data
		for node in self.metadata["response_parse_tree_track"]:
			try:
				res = res[node]
			except:
				return None
		return res





### useful stuff

def utf(st):
	return st.encode(encoding="UTF-8")
def b64(inp):
	return base64.b64encode(inp)



### actually create everything

__all__ = [
	"lastfm",
	"spotify",
	"musicbrainz"
]
from . import *


services["metadata"].sort(
	key=lambda provider : get_settings("METADATA_PROVIDERS").index(provider.identifier)
)
