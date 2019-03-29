import os

## decorator to set default arguments that are only evaluated at runtime
def defaultarguments(defaultdict,**defaultargs):
	def decorator(func):	#actual decorator function
		def newfunc(*args,**kwargs):
			realargs = {}

			# evaluate default values at runtime
			for k in defaultargs:
				realargs[k] = defaultdict[defaultargs[k]]

			# overwrite given arguments of function
			realargs.update(kwargs)

			# execute function with correct arguments
			return func(*args,**realargs)

		return newfunc

	return decorator


## opens file, creates it if necessary (including all folders)
def gopen(filepath,mode):
	directory = os.path.dirname(filepath)
	os.makedirs(directory, exist_ok=True)

	return open(filepath,mode)
