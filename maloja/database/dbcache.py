# the more generalized caching for DB queries
# mostly to avoid long loading times for pages that show lots of information
# that changes very infrequently or not at all

import lru
import json
from doreah.regular import runhourly
from doreah.logging import log


USE_CACHE = True
cache = lru.LRU(300000)

@runhourly
def print_stats():
	log(f"Cache Size: {len(cache)}")

def cached_wrapper(inner_func):
	def outer_func(**kwargs):
		key = (serialize(kwargs), inner_func, kwargs.get("since"), kwargs.get("to"))

		if USE_CACHE and key in cache:
			return cache.get(key)

		else:
			result = inner_func(**kwargs)
			cache[key] = result
			return result

	return outer_func



def invalidate_caches(scrobbletime):
	for k in cache.keys():
		if (k[2] is None or scrobbletime >= k[2]) and (k[3] is None or scrobbletime <= k[3]):
			del cache[k]







def serialize(obj):
	try:
		return serialize(obj.hashable())
	except:
		try:
			return json.dumps(obj)
		except:
			if isinstance(obj, (list, tuple)):
				return "[" + ",".join(serialize(o) for o in obj) + "]"
			elif isinstance(obj,dict):
				return "{" + ",".join(serialize(o) + ":" + serialize(obj[o]) for o in obj) + "}"
			return json.dumps(obj.hashable())
