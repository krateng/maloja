from ..globalconf import apikeystore

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
