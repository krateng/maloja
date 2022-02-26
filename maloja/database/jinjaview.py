
from .. import database

# this is a wrapper object that provides a DB connection so that one jinja page
# (with all its included partials) can use it for all functions
# it also translates the non-unpacked calls to unpacked calls that the DB wants
class JinjaDBConnection:
	def __init__(self):
		pass
	def __getattr__(self,name):
		originalmethod = getattr(database,name)

		def packedmethod(*keys):
			kwargs = {}
			for k in keys:
				kwargs.update(k)
			return originalmethod(**kwargs)

		return packedmethod
