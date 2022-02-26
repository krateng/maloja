
from .. import database
from . sqldb import engine


# this is a wrapper object that provides a DB connection so that one jinja page
# (with all its included partials) can use it for all functions
# it also translates the non-unpacked calls to unpacked calls that the DB wants
class JinjaDBConnection:
	def __enter__(self):
		self.conn = engine.connect()
		return self
	def __exit__(self, exc_type, exc_value, exc_traceback):
		self.conn.close()
	def __getattr__(self,name):
		originalmethod = getattr(database,name)

		def packedmethod(*keys):
			kwargs = {}
			for k in keys:
				kwargs.update(k)
			return originalmethod(**kwargs,dbconn=self.conn)

		return packedmethod
