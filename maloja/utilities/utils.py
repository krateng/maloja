import json


#####
## SERIALIZE
#####

def serialize(obj):
	try:
		return serialize(obj.hashable())
	except:
		try:
			return json.dumps(obj)
		except:
			if isinstance(obj,list) or isinstance(obj,tuple):
				return "[" + ",".join(serialize(o) for o in obj) + "]"
			elif isinstance(obj,dict):
				return "{" + ",".join(serialize(o) + ":" + serialize(obj[o]) for o in obj) + "}"
			return json.dumps(obj.hashable())


	#if isinstance(obj,list) or if isinstance(obj,tuple):
	#	return "[" + ",".join(dumps(o) for o in obj) + "]"
	#if isinstance(obj,str)
