from bottle import HTTPError

class EntityExists(Exception):
	def __init__(self,entitydict):
		self.entitydict = entitydict


class TrackExists(EntityExists):
	pass

class ArtistExists(EntityExists):
	pass


class DatabaseNotBuilt(HTTPError):
	def __init__(self):
		super().__init__(
			status=503,
			body="The Maloja Database is being upgraded to Version 3. This could take quite a long time! (~ 2-5 minutes per 10 000 scrobbles)",
			headers={"Retry-After":120}
		)


class MissingScrobbleParameters(Exception):
	def __init__(self,params=[]):
		self.params = params

class MissingEntityParameter(Exception):
	pass
