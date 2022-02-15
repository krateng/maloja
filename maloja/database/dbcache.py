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

	def outer_func(**kwargs):
		global hits, misses
		key = (serialize(kwargs), inner_func, kwargs.get("since"), kwargs.get("to"))

		if USE_CACHE and key in cache:
			hits += 1
			return cache.get(key)

		else:
			misses += 1
			result = inner_func(**kwargs)
			cache[key] = result
			return result

	return outer_func



def invalidate_caches(scrobbletime):
	for k in cache.keys():
		if (k[2] is None or scrobbletime >= k[2]) and (k[3] is None or scrobbletime <= k[3]):
			del cache[k]



def trim_cache():
	ramprct = psutil.virtual_memory().percent
	if ramprct > malojaconfig["DB_MAX_MEMORY"]:
		log(f"{ramprct}% RAM usage, reducing caches!")
		ratio = (malojaconfig["DB_MAX_MEMORY"] / ramprct) ** 3
		targetsize = max(int(len(cache) * ratio),100)
		c.set_size(targetsize)
		c.set_size(HIGH_NUMBER)
		log(f"New RAM usage: {psutil.virtual_memory().percent}%")


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
