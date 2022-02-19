# the more generalized caching for DB queries
# mostly to avoid long loading times for pages that show lots of information
# that changes very infrequently or not at all

import lru
import psutil
import json
from doreah.regular import runhourly
from doreah.logging import log

from ..globalconf import malojaconfig

USE_CACHE = True
HIGH_NUMBER = 1000000

cache = lru.LRU(HIGH_NUMBER)
hits, misses = 0, 0



@runhourly
def print_stats():
	log(f"Cache Size: {len(cache)}, RAM Utilization: {psutil.virtual_memory().percent}%, Cache Hits: {hits}/{hits+misses}")
	trim_cache()


def cached_wrapper(inner_func):

	if not USE_CACHE: return inner_func
	def outer_func(*args,**kwargs):
		global hits, misses
		key = (serialize(args),serialize(kwargs), inner_func, kwargs.get("since"), kwargs.get("to"))

		if key in cache:
			hits += 1
			return cache.get(key)

		else:
			misses += 1
			result = inner_func(*args,**kwargs)
			cache[key] = result
			return result

	return outer_func



def invalidate_caches(scrobbletime):
	cleared, kept = 0, 0
	for k in cache.keys():
		if (k[3] is None or scrobbletime >= k[3]) and (k[4] is None or scrobbletime <= k[4]):
			cleared += 1
			del cache[k]
		else:
			kept += 1
	log(f"Invalidated {cleared} of {cleared+kept} DB cache entries")



def trim_cache():
	ramprct = psutil.virtual_memory().percent
	if ramprct > malojaconfig["DB_MAX_MEMORY"]:
		log(f"{ramprct}% RAM usage, reducing caches!")
		ratio = (malojaconfig["DB_MAX_MEMORY"] / ramprct) ** 3
		targetsize = max(int(len(cache) * ratio),100)
		cache.set_size(targetsize)
		cache.set_size(HIGH_NUMBER)
		log(f"New RAM usage: {psutil.virtual_memory().percent}%")



def serialize(obj):
	try:
		return serialize(obj.hashable())
	except:
		try:
			return json.dumps(obj)
		except:
			if isinstance(obj, (list, tuple, set)):
				return "[" + ",".join(serialize(o) for o in obj) + "]"
			elif isinstance(obj,dict):
				return "{" + ",".join(serialize(o) + ":" + serialize(obj[o]) for o in obj) + "}"
			return json.dumps(obj.hashable())
