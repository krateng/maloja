
###
## Caches in front of DB
## the volatile caches are intended mainly for excessive site navigation during one session
## the permanent caches are there to save data that is hard to calculate and never changes (old charts)
###

import psutil
import copy
import lru

from doreah.logging import log

from ..globalconf import malojaconfig
from .. import utilities
from .. import database as dbmain

if malojaconfig["USE_DB_CACHE"]:
	def db_query(**kwargs):
		return db_query_cached(**kwargs)
	def db_aggregate(**kwargs):
		return db_aggregate_cached(**kwargs)
else:
	def db_query(**kwargs):
		return dbmain.db_query_full(**kwargs)
	def db_aggregate(**kwargs):
		return dbmain.db_aggregate_full(**kwargs)


csz = malojaconfig["DB_CACHE_ENTRIES"]
cmp = malojaconfig["DB_MAX_MEMORY"]

cache_query = lru.LRU(csz)
cache_query_perm = lru.LRU(csz)
cache_aggregate = lru.LRU(csz)
cache_aggregate_perm = lru.LRU(csz)

perm_caching = malojaconfig["CACHE_DATABASE_PERM"]
temp_caching = malojaconfig["CACHE_DATABASE_SHORT"]

cachestats = {
	"cache_query":{
		"hits_perm":0,
		"hits_tmp":0,
		"misses":0,
		"objperm":cache_query_perm,
		"objtmp":cache_query,
		"name":"Query Cache"
	},
	"cache_aggregate":{
		"hits_perm":0,
		"hits_tmp":0,
		"misses":0,
		"objperm":cache_aggregate_perm,
		"objtmp":cache_aggregate,
		"name":"Aggregate Cache"
	}
}

from doreah.regular import runhourly

@runhourly
def log_stats():
	logstr = "{name}: {hitsperm} Perm Hits, {hitstmp} Tmp Hits, {misses} Misses; Current Size: {sizeperm}/{sizetmp}"
	for s in (cachestats["cache_query"],cachestats["cache_aggregate"]):
		log(logstr.format(name=s["name"],hitsperm=s["hits_perm"],hitstmp=s["hits_tmp"],misses=s["misses"],
		sizeperm=len(s["objperm"]),sizetmp=len(s["objtmp"])),module="debug")

def db_query_cached(**kwargs):
	global cache_query, cache_query_perm
	key = utilities.serialize(kwargs)

	eligible_permanent_caching = (
		"timerange" in kwargs and
		not kwargs["timerange"].active() and
		perm_caching
	)
	eligible_temporary_caching = (
		not eligible_permanent_caching and
		temp_caching
	)

	# hit permanent cache for past timeranges
	if eligible_permanent_caching and key in cache_query_perm:
		cachestats["cache_query"]["hits_perm"] += 1
		return copy.copy(cache_query_perm.get(key))

	# hit short term cache
	elif eligible_temporary_caching and key in cache_query:
		cachestats["cache_query"]["hits_tmp"] += 1
		return copy.copy(cache_query.get(key))

	else:
		cachestats["cache_query"]["misses"] += 1
		result = dbmain.db_query_full(**kwargs)
		if eligible_permanent_caching: cache_query_perm[key] = result
		elif eligible_temporary_caching: cache_query[key] = result

		reduce_caches_if_low_ram()

		return result


def db_aggregate_cached(**kwargs):
	global cache_aggregate, cache_aggregate_perm
	key = utilities.serialize(kwargs)

	eligible_permanent_caching = (
		"timerange" in kwargs and
		not kwargs["timerange"].active() and
		perm_caching
	)
	eligible_temporary_caching = (
		not eligible_permanent_caching and
		temp_caching
	)

	# hit permanent cache for past timeranges
	if eligible_permanent_caching and key in cache_aggregate_perm:
		cachestats["cache_aggregate"]["hits_perm"] += 1
		return copy.copy(cache_aggregate_perm.get(key))

	# hit short term cache
	elif eligible_temporary_caching and key in cache_aggregate:
		cachestats["cache_aggregate"]["hits_tmp"] += 1
		return copy.copy(cache_aggregate.get(key))

	else:
		cachestats["cache_aggregate"]["misses"] += 1
		result = dbmain.db_aggregate_full(**kwargs)
		if eligible_permanent_caching: cache_aggregate_perm[key] = result
		elif eligible_temporary_caching: cache_aggregate[key] = result

		reduce_caches_if_low_ram()

		return result

def invalidate_caches():
	global cache_query, cache_aggregate
	cache_query.clear()
	cache_aggregate.clear()
	log("Database caches invalidated.")

def reduce_caches(to=0.75):
	global cache_query, cache_aggregate, cache_query_perm, cache_aggregate_perm
	for c in cache_query, cache_aggregate, cache_query_perm, cache_aggregate_perm:
		currentsize = len(c)
		if currentsize > 100:
			targetsize = max(int(currentsize * to),10)
			c.set_size(targetsize)
			c.set_size(csz)

def reduce_caches_if_low_ram():
	ramprct = psutil.virtual_memory().percent
	if ramprct > cmp:
		log("{prct}% RAM usage, reducing caches!".format(prct=ramprct),module="debug")
		ratio = (cmp / ramprct) ** 3
		reduce_caches(to=ratio)
