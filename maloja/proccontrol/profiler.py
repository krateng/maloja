import cProfile, pstats
profiler = cProfile.Profile()



def profile(func):
	def newfunc(*args,**kwargs):
		profiler.enable()
		result = func(*args,**kwargs)
		profiler.disable()
		pstats.Stats(profiler).dump_stats(f"dev/benchmarking/{func}.stats")
		return result

	return newfunc
