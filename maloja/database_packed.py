from . import database

# this is simply an object to expose all database functions with their arguments packed into dicts
# because jinja doesn't accept **kwargs
class DB:
	def __getattr__(self,name):
		originalmethod = getattr(database,name)

		def packedmethod(*keys):
			kwargs = {}
			for k in keys:
				kwargs.update(k)
			return originalmethod(**kwargs)

		return packedmethod


# class that is initialized with all the uri keys of the currently requested page and exposes curried db functions
class View:
	def __init__(self,filterkeys,limitkeys,delimitkeys,amountkeys):
		self.filterkeys = filterkeys
		self.limitkeys = limitkeys
		self.delimitkeys = delimitkeys
		self.amountkeys = amountkeys


	def get_pulse(self):
		return database.get_pulse(**self.limitkeys,**self.delimitkeys,**self.filterkeys)
