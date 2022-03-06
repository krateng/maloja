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
def api_key_correct(request):
	request.malojaclient = None
	args = request.params
	try:
		args.update(request.json)
	except:
		pass
	if "key" in args:
		apikey = args.pop("key")
	elif "apikey" in args:
		apikey = args.pop("apikey")
	else: return False
	if checkAPIkey(apikey):
		request.malojaclient = [c for c in apikeystore if apikeystore[c]==apikey][0]
		return True
	else:
		return False


def checkAPIkey(key):
	return apikeystore.check_key(key)
def allAPIkeys():
	return [apikeystore[k] for k in apikeystore]
