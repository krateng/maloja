### API KEYS
### symmetric keys are fine since we hopefully use HTTPS

from doreah.keystore import KeyStore
from doreah.logging import log

from ..pkg_global.conf import data_dir

apikeystore = KeyStore(file=data_dir['clients']("apikeys.yml"),save_endpoint="/apis/mlj_1/apikeys")


from .. import upgrade
upgrade.upgrade_apikeys()


# skip regular authentication if api key is present in request
# an api key now ONLY permits scrobbling tracks, no other admin tasks
def api_key_correct(request,args,kwargs):
	if "key" in kwargs:
		apikey = kwargs.pop("key")
	elif "apikey" in kwargs:
		apikey = kwargs.pop("apikey")
	else: return False

	client = apikeystore.check_and_identify_key(apikey)
	if client:
		return {'client':client}
	else:
		return False
