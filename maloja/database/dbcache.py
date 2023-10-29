# the more generalized caching for DB queries
# mostly to avoid long loading times for pages that show lots of information
# that changes very infrequently or not at all

import lru
import psutil
import json
import sys
from doreah.regular import runhourly
from doreah.logging import log

from ..pkg_global.conf import malojaconfig
from . import no_aux_mode


if malojaconfig['USE_GLOBAL_CACHE']:

	cache = lru.LRU(10000)
	entitycache = lru.LRU(100000)



	@runhourly
	@no_aux_mode
	def maintenance():
		print_stats()
		trim_cache()

	def print_stats():
		for name,c in (('Cache',cache),('Entity Cache',entitycache)):
			hits, misses = c.get_stats()
			log(f"{name}: Size: {len(c)} | Hits: {hits}/{hits+misses} | Estimated Memory: {human_readable_size(c)}")
		log(f"System RAM Utilization: {psutil.virtual_memory().percent}%")


	def cached_wrapper(inner_func):

		def outer_func(*args,**kwargs):

			if 'dbconn' in kwargs:
				conn = kwargs.pop('dbconn')
			else:
				conn = None
			global hits, misses
			key = (serialize(args),serialize(kwargs), inner_func, kwargs.get("since"), kwargs.get("to"))
			# TODO: also factor in default values to get better chance of hits

			try:
				return cache[key]
			except KeyError:
				result = inner_func(*args,**kwargs,dbconn=conn)
				cache[key] = result
				return result

		outer_func.__name__ = f"CACHD_{inner_func.__name__}"

		return outer_func


	# cache for functions that call with a whole list of entity ids
	# we don't want a new cache entry for every single combination, but keep a common
	# cache that's aware of what we're calling
	def cached_wrapper_individual(inner_func):

		def outer_func(set_arg,**kwargs):
			if 'dbconn' in kwargs:
				conn = kwargs.pop('dbconn')
			else:
				conn = None

			result = {}
			for id in set_arg:
				try:
					result[id] = entitycache[(inner_func,id)]
				except KeyError:
					pass

			remaining = inner_func(set(e for e in set_arg if e not in result),dbconn=conn)
			for id in remaining:
					entitycache[(inner_func,id)] = remaining[id]
					result[id] = remaining[id]

			return result

		return outer_func

	@no_aux_mode
	def invalidate_caches(scrobbletime=None):

		cleared, kept = 0, 0
		for k in cache.keys():
			# VERY BIG TODO: differentiate between None as in 'unlimited timerange' and None as in 'time doesnt matter here'!
			if scrobbletime is None or ((k[3] is None or scrobbletime >= k[3]) and (k[4] is None or scrobbletime <= k[4])):
				cleared += 1
				del cache[k]
			else:
				kept += 1
		log(f"Invalidated {cleared} of {cleared+kept} DB cache entries")

	@no_aux_mode
	def invalidate_entity_cache():
		entitycache.clear()

	def trim_cache():
		ramprct = psutil.virtual_memory().percent
		if ramprct > malojaconfig["DB_MAX_MEMORY"]:
			log(f"{ramprct}% RAM usage, clearing cache!")
			for c in (cache,entitycache):
				c.clear()
			#ratio = 0.6
			#targetsize = max(int(len(cache) * ratio),50)
			#log(f"Reducing to {targetsize} entries")
			#cache.set_size(targetsize)
			#cache.set_size(HIGH_NUMBER)
			#if cache.get_size() > CACHE_ADJUST_STEP:
			#	cache.set_size(cache.get_size() - CACHE_ADJUST_STEP)

			#log(f"New RAM usage: {psutil.virtual_memory().percent}%")
			print_stats()






else:
	def cached_wrapper(func):
		return func
	def cached_wrapper_individual(func):
		return func
	def invalidate_caches(scrobbletime=None):
		return None
	def invalidate_entity_cache():
		return None


def serialize(obj):
	try:
		return serialize(obj.hashable())
	except AttributeError:
		try:
			return json.dumps(obj)
		except Exception:
			if isinstance(obj, (list, tuple, set)):
				return "[" + ",".join(serialize(o) for o in obj) + "]"
			elif isinstance(obj,dict):
				return "{" + ",".join(serialize(o) + ":" + serialize(obj[o]) for o in obj) + "}"
			return json.dumps(obj.hashable())



def get_size_of(obj,counted=None):
	if counted is None:
		counted = set()
	if id(obj) in counted: return 0
	size = sys.getsizeof(obj)
	counted.add(id(obj))
	try:
		for k,v in obj.items():
			size += get_size_of(v,counted=counted)
	except:
		try:
			for i in obj:
				size += get_size_of(i,counted=counted)
		except:
			pass
	return size

def human_readable_size(obj):
	units = ['','Ki','Mi','Gi','Ti','Pi']
	magnitude = 0

	bytes = get_size_of(obj)
	while bytes > 1024 and len(units) > magnitude+1:
		bytes = bytes / 1024
		magnitude += 1

	if magnitude > 2:
		return f"{bytes:.2f} {units[magnitude]}B"
	else:
		return f"{bytes:.0f} {units[magnitude]}B"
