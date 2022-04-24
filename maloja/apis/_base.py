from nimrodel import EAPI as API
from nimrodel import Multi

from ._exceptions import *

from copy import deepcopy
from types import FunctionType
import sys
import datetime

from doreah.logging import log

from bottle import response

from ..cleanup import CleanerAgent
from .. import database

__logmodulename__ = "apis"


#def singleton(cls):
#	return cls()



cla = CleanerAgent()

class APIHandler:
	# make these classes singletons
	_instance = None
	def __new__(cls, *args, **kwargs):
		if not isinstance(cls._instance, cls):
			cls._instance = object.__new__(cls, *args, **kwargs)
		return cls._instance

	def __init_subclass__(cls):
		# Copy the handle function so we can have a unique docstring
		sf = cls.__base__.wrapper
		cls.wrapper = FunctionType(sf.__code__,sf.__globals__,sf.__name__,sf.__defaults__,sf.__closure__)
		cls.wrapper.__annotations__ = sf.__annotations__
		# need to copy annotations so nimrodel properly passes path argument

		# create docstring
		doc = "Accepts requests according to the <a href='{link}'>{name} Standard</a>"
		cls.wrapper.__doc__ = doc.format(name=cls.__apiname__,link=cls.__doclink__)

	def __init__(self):
		self.init()

		# creates a rump api object that exposes one generic endpoint
		# we don't want the api explorer to show the different structures of
		# third party apis, just mention they exist
		self.nimrodelapi = API(delay=True)
		self.nimrodelapi.get("{path}",pass_headers=True)(self.wrapper)
		self.nimrodelapi.post("{path}",pass_headers=True)(self.wrapper)
		self.nimrodelapi.get("",pass_headers=True)(self.wrapper)
		self.nimrodelapi.post("",pass_headers=True)(self.wrapper)


	def wrapper(self,path:Multi=[],**keys):
		log(f"{self.__apiname__} API request: {path}")# + " | Keys: " + str({k:keys.get(k) for k in keys}))

		try:
			response.status,result = self.handle(path,keys)
		except Exception:
			exceptiontype = sys.exc_info()[0]
			if exceptiontype in self.errors:
				response.status,result = self.errors[exceptiontype]
				log(f"Error with {self.__apiname__} API: {exceptiontype} (Request: {path})")
			else:
				response.status,result = 500,{"status":"Unknown error","code":500}
				log(f"Unhandled Exception with {self.__apiname__} API: {exceptiontype} (Request: {path})")

		return result
		#else:
		#	result = {"error":"Invalid scrobble protocol"}
		#	response.status = 500


	def handle(self,path,keys):

		try:
			methodname = self.get_method(path,keys)
			method = self.methods[methodname]
		except Exception:
			log("Could not find a handler for method " + str(methodname) + " in API " + self.__apiname__,module="debug")
			log("Keys: " + str(keys),module="debug")
			raise InvalidMethodException()
		return method(path,keys)


	def scrobble(self,rawscrobble,client=None):

		# fixing etc is handled by the main scrobble function
		try:
			return database.incoming_scrobble(rawscrobble,api=self.__apiname__,client=client)
		except Exception:
			raise ScrobblingException()
