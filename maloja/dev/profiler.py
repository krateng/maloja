import os

import cProfile, pstats

from doreah.logging import log
from doreah.timing import Clock

from ..pkg_global.conf import data_dir


profiler = cProfile.Profile()

FULL_PROFILE = False

def profile(func):
	def newfunc(*args,**kwargs):

		if FULL_PROFILE:
			benchmarkfolder = data_dir['logs']("benchmarks")
			os.makedirs(benchmarkfolder,exist_ok=True)

		clock = Clock()
		clock.start()

		if FULL_PROFILE:
			profiler.enable()
		result = func(*args,**kwargs)
		if FULL_PROFILE:
			profiler.disable()

		log(f"Executed {func.__name__} ({args}, {kwargs}) in {clock.stop():.2f}s",module="debug_performance")
		if FULL_PROFILE:
			try:
				pstats.Stats(profiler).dump_stats(os.path.join(benchmarkfolder,f"{func.__name__}.stats"))
			except Exception:
				pass

		return result

	return newfunc
