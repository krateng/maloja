import time

from ._internal import defaultarguments, doreahconfig

_config = {}


# set configuration
# si		0 means seconds, 1 ms, 2 μs, 3 ns etc
def config(si=0):
	global _config
	_config["si"] = si


# initial config on import, set everything to default
config()


# Take clock. Returns time passed since last call of this function. if called with an identifier, will only
# consider calls with that identifier. No identifier means any call is valid.
# identifiers	arbitrary strings to remember different timers. guaranteed to set all timers to exactly the same time for
#				all identifiers in one call. will return tuple of all identifiers, singular value if only one identifier
def clock(*identifiers,lastcalls={None:None}):

	if len(identifiers) == 0: identifiers = (None,)

	now = time.time()
	# get last calls
	stamps = (lastcalls.get(i) for i in identifiers)
	results = tuple(None if lc is None else (now - lc) * (1000**_config["si"]) for lc in stamps)
	if len(results) == 1: results = results[0]

	# set new stamps
	for i in identifiers:
		lastcalls[i] = now
	lastcalls[None] = now			# always save last overall call so we can directly access it

	return results



def clockp(name,*identifiers):
	time = clock(*identifiers)
	print(name + ": " + str(time))






# now check local configuration file
_config.update(doreahconfig("timing"))
