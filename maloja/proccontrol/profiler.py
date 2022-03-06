import cProfile, pstats
profiler = cProfile.Profile()



def profile(func):
	def newfunc(*args,**kwargs):
		profiler.enable()
		result = func(*args,**kwargs)
		profiler.disable()
		try:
			pstats.Stats(profiler).dump_stats(f"dev/benchmarking/{func.__name__}.stats")
		except:
			pass
		return result

	return newfunc
