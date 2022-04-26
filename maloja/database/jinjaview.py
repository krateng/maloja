from .. import database
from . sqldb import engine

from .dbcache import serialize

from ..pkg_global.conf import malojaconfig

from doreah.logging import log


# this is a wrapper object that provides a DB connection so that one jinja page
# (with all its included partials) can use it for all functions
# it also translates the non-unpacked calls to unpacked calls that the DB wants
# it also maintains a request-local cache since many webpages use the same stats
# several times
class JinjaDBConnection:
	def __init__(self):
		self.cache = {}
		self.hits = 0
		self.misses = 0
	def __enter__(self):
		self.conn = engine.connect()
		return self
	def __exit__(self, exc_type, exc_value, exc_traceback):
		self.conn.close()
		if malojaconfig['USE_REQUEST_CACHE']:
			log(f"Generated page with {self.hits}/{self.hits+self.misses} local Cache hits",module="debug_performance")
		del self.cache
	def __getattr__(self,name):
		originalmethod = getattr(database,name)

		def packedmethod(*keys):
			kwargs = {}
			for k in keys:
				kwargs.update(k)
			if malojaconfig['USE_REQUEST_CACHE']:
				cachekey = serialize((id(originalmethod),kwargs))
				if cachekey in self.cache:
					self.hits += 1
					return self.cache[cachekey]
				else:
					self.misses += 1
					result = originalmethod(**kwargs,dbconn=self.conn)
					self.cache[cachekey] = result
					return result
			else:
				result = originalmethod(**kwargs,dbconn=self.conn)
				return result


		return packedmethod
