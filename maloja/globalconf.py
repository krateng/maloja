from doreah.settings import get_settings

THUMBOR_SERVER, THUMBOR_SECRET = get_settings("THUMBOR_SERVER","THUMBOR_SECRET")
try:
	USE_THUMBOR = THUMBOR_SERVER is not None and THUMBOR_SECRET is not None
	if USE_THUMBOR:
		from libthumbor import CryptoURL
		THUMBOR_GENERATOR = CryptoURL(key=THUMBOR_SECRET)
		OWNURL = get_settings("PUBLIC_URL")
		assert OWNURL is not None
except:
	USE_THUMBOR = False
	log("Thumbor could not be initialized. Is libthumbor installed?")
