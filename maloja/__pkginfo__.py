# This file has now been slighly repurposed and will simply give other parts of
# the package access to some global meta-information about itself

try:
	# from source
	import toml
	with open("./pyproject.toml") as filed:
		metadata = toml.load(filed)['project']
		VERSIONSTR = metadata['version']
		HOMEPAGE = metadata['urls']['homepage']
except:
	# package distributrion
	from importlib import metadata
	VERSIONSTR = metadata.version('maloja')
	urls = metadata.metadata('maloja').get_all('Project-URL')
	urls = [e.split(', ') for e in urls]
	HOMEPAGE = [e[1] for e in urls if e[0] == 'homepage'][0]


VERSION = VERSIONSTR.split('.')


USER_AGENT = f"Maloja/{VERSIONSTR} ( {HOMEPAGE} )"
