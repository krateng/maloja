# This file has now been slighly repurposed and will simply give other parts of
# the package access to some global meta-information about itself

try:
	# from source
	import toml
	with open("./pyproject.toml") as filed:
		metadata = toml.load(filed)['project']
		VERSION = metadata['version'] + "-dev"
		HOMEPAGE = metadata['urls']['homepage']
	# this will give wrong info when the installed package is run, but we just
	# happen to be in the directory of the project
	# but this can't be helped I think
except:

	# package distributrion
	from pkg_resources import get_distribution
	pkg = get_distribution('maloja')  # also contains a metadata
	VERSION = pkg.version

	#urls = metadata.metadata('maloja').get_all('Project-URL')
	#urls = [e.split(', ') for e in urls]
	#HOMEPAGE = [e[1] for e in urls if e[0] == 'homepage'][0]
	# hardcode this for now
	HOMEPAGE = "https://github.com/krateng/maloja"


USER_AGENT = f"Maloja/{VERSION} ( {HOMEPAGE} )"
