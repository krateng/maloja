from simplejson import JSONEncoder

def newdefault(self,object):
	return getattr(object.__class__,"__json__", olddefault)(object)

olddefault = JSONEncoder.default
JSONEncoder.default = newdefault
