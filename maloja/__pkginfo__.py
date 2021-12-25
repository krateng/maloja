# This file has now been slighly repurposed and will simply give other parts of
# the package access to some global meta-information about itself

try:
	# package distributrion
	import pkg_resources
	self = pkg_resources.get_distribution('maloja')
	metadata = {'version':self.version}
except:
	# from source
	import toml
	with open("./pyproject.toml") as filed:
		metadata = toml.load(filed)['project']

versionstr = metadata['version']
version = versionstr.split('.')
urls = {
	"repo":"https://github.com/krateng/maloja"
}
user_agent = f"Maloja/{versionstr} ( {urls['repo']} )"
