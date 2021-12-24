# This file has now been slighly repurposed and will simply give other parts of
# the package access to some global meta-information about itself

import pkg_resources
self = pkg_resources.get_distribution('maloja')

versionstr = self.version
version = self.version.split('.')
urls = {
	"repo":"https://github.com/krateng/maloja"
}
user_agent = f"Maloja/{versionstr} ( {urls['repo']} )"
