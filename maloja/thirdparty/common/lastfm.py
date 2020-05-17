import hashlib
import urllib

class LastFMInterface:
	def query_compose(self,parameters):
		m = hashlib.md5()
		keys = sorted(str(k) for k in parameters)
		m.update(self.utf("".join(str(k) + str(parameters[k]) for k in keys)))
		m.update(self.utf(get_settings("LASTFM_API_SECRET")))
		sig = m.hexdigest()
		return urllib.parse.urlencode(parameters) + "&api_sig=" + sig

	def utf(self,st):
		return st.encode(encoding="UTF-8")
