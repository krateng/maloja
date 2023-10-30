# custom json encoding



def newdefault(self,object):
	return getattr(object.__class__,"__json__", self._olddefault)(object)


# just patch every encoder
try:
	from simplejson import JSONEncoder
	JSONEncoder._olddefault = JSONEncoder.default
	JSONEncoder.default = newdefault
except Exception:
	pass

try:
	from json import JSONEncoder
	JSONEncoder._olddefault = JSONEncoder.default
	JSONEncoder.default = newdefault
except Exception:
	pass

try:
	from ujson import JSONEncoder
	JSONEncoder._olddefault = JSONEncoder.default
	JSONEncoder.default = newdefault
except Exception:
	pass

