### API KEYS
### symmetric keys are fine since we hopefully use HTTPS

from doreah.keystore import KeyStore
from doreah.logging import log

from ..globalconf import data_dir

apikeystore = KeyStore(file=data_dir['clients']("apikeys.yml"),save_endpoint="/apis/mlj_1/apikeys")
from .. import upgrade
upgrade.upgrade_apikeys()

log("Authenticated Machines: " + ", ".join([k for k in apikeystore]),module='apis')

# skip regular authentication if api key is present in request
# an api key now ONLY permits scrobbling tracks, no other admin tasks
def api_key_correct(request,args,kwargs):
	if "key" in kwargs:
		apikey = kwargs.pop("key")
	elif "apikey" in kwargs:
		apikey = kwargs.pop("apikey")
	else: return False
	if checkAPIkey(apikey):
		client = [c for c in apikeystore if apikeystore[c]==apikey][0]
		return {'client':client}
	else:
		return False


def checkAPIkey(key):
	return apikeystore.check_key(key)
def allAPIkeys():
	return [apikeystore[k] for k in apikeystore]
