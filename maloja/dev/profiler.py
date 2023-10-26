import os

import cProfile, pstats

from doreah.logging import log
from doreah.timing import Clock

from ..pkg_global.conf import data_dir




FULL_PROFILE = False
SINGLE_CALLS = False
# only save the last single call instead of adding up all calls
# of that function for more representative performance result

if SINGLE_CALLS:
	profiler = cProfile.Profile()

def profile(func):
	def newfunc(*args,**kwargs):

		clock = Clock()
		clock.start()

		if FULL_PROFILE:
			benchmarkfolder = data_dir['logs']("benchmarks")
			os.makedirs(benchmarkfolder,exist_ok=True)
			if not SINGLE_CALLS:
				localprofiler = cProfile.Profile()
			else:
				localprofiler = profiler
			localprofiler.enable()

		result = func(*args,**kwargs)

		if FULL_PROFILE:
			localprofiler.disable()

		seconds = clock.stop()
		realfunc = func
		while(hasattr(realfunc,'__innerfunc__')):
			realfunc = realfunc.__innerfunc__
		log(f"Executed {realfunc.__name__} ({args}, {kwargs}) in {seconds:.2f}s",module="debug_performance")
		if FULL_PROFILE:
			targetfilename = os.path.join(benchmarkfolder,f"{realfunc.__name__}.stats")
			try:
				pstats.Stats(localprofiler).dump_stats(targetfilename)
				log(f"Saved benchmark as {targetfilename}")
			except Exception:
				log(f"Failed to save benchmark as {targetfilename}")

		return result

	return newfunc
