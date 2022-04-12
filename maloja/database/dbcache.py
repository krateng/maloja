# the more generalized caching for DB queries
# mostly to avoid long loading times for pages that show lots of information
# that changes very infrequently or not at all

import lru
import psutil
import json
from doreah.regular import runhourly
from doreah.logging import log

from ..globalconf import malojaconfig

HIGH_NUMBER = 1000000
CACHE_SIZE = 10000
ENTITY_CACHE_SIZE = 1000000
CACHE_ADJUST_STEP = 100

cache = lru.LRU(CACHE_SIZE)
entitycache = lru.LRU(ENTITY_CACHE_SIZE)

hits, misses = 0, 0



@runhourly
def maintenance():
	if malojaconfig['USE_GLOBAL_CACHE']:
		print_stats()
		trim_cache()

def print_stats():
	log(f"Cache Size: {len(cache)} [{len(entitycache)} E], System RAM Utilization: {psutil.virtual_memory().percent}%, Cache Hits: {hits}/{hits+misses}")
	#print("Full rundown:")
	#import sys
	#for k in cache.keys():
	#	print(f"\t{k}\t{sys.getsizeof(cache[k])}")


def cached_wrapper(inner_func):

	if not malojaconfig['USE_GLOBAL_CACHE']: return inner_func
	def outer_func(*args,**kwargs):
		if 'dbconn' in kwargs:
			conn = kwargs.pop('dbconn')
		else:
			conn = None
		global hits, misses
		key = (serialize(args),serialize(kwargs), inner_func, kwargs.get("since"), kwargs.get("to"))

		if key in cache:
			hits += 1
			return cache.get(key)

		else:
			misses += 1
			result = inner_func(*args,**kwargs,dbconn=conn)
			cache[key] = result
			return result

	return outer_func


# cache for functions that call with a whole list of entity ids
# we don't want a new cache entry for every single combination, but keep a common
# cache that's aware of what we're calling
def cached_wrapper_individual(inner_func):

	if not malojaconfig['USE_GLOBAL_CACHE']: return inner_func
	def outer_func(set_arg,**kwargs):


		if 'dbconn' in kwargs:
			conn = kwargs.pop('dbconn')
		else:
			conn = None

		#global hits, misses
		result = {}
		for id in set_arg:
			if (inner_func,id) in entitycache:
				result[id] = entitycache[(inner_func,id)]
				#hits += 1
			else:
				pass
				#misses += 1


		remaining = inner_func(set(e for e in set_arg if e not in result),dbconn=conn)
		for id in remaining:
				entitycache[(inner_func,id)] = remaining[id]
				result[id] = remaining[id]

		return result

	return outer_func

def invalidate_caches(scrobbletime):
	if malojaconfig['USE_GLOBAL_CACHE']:
		cleared, kept = 0, 0
		for k in cache.keys():
			# VERY BIG TODO: differentiate between None as in 'unlimited timerange' and None as in 'time doesnt matter here'!
			if (k[3] is None or scrobbletime >= k[3]) and (k[4] is None or scrobbletime <= k[4]):
				cleared += 1
				del cache[k]
			else:
				kept += 1
		log(f"Invalidated {cleared} of {cleared+kept} DB cache entries")


def invalidate_entity_cache():
	entitycache.clear()


def trim_cache():
	ramprct = psutil.virtual_memory().percent
	if ramprct > malojaconfig["DB_MAX_MEMORY"]:
		log(f"{ramprct}% RAM usage, clearing cache and adjusting size!")
		#ratio = 0.6
		#targetsize = max(int(len(cache) * ratio),50)
		#log(f"Reducing to {targetsize} entries")
		#cache.set_size(targetsize)
		#cache.set_size(HIGH_NUMBER)
		cache.clear()
		if cache.get_size() > CACHE_ADJUST_STEP:
			cache.set_size(cache.get_size() - CACHE_ADJUST_STEP)

		#log(f"New RAM usage: {psutil.virtual_memory().percent}%")
		print_stats()



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
