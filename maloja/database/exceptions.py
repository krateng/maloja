from bottle import HTTPError

class EntityExists(Exception):
	def __init__(self,entitydict):
		self.entitydict = entitydict


class TrackExists(EntityExists):
	pass

class ArtistExists(EntityExists):
	pass

class AlbumExists(EntityExists):
	pass

class DatabaseNotBuilt(HTTPError):
	def __init__(self):
		super().__init__(
			status=503,
			body="The Maloja Database is being upgraded to support new Maloja features. This could take a while.",
			headers={"Retry-After":120}
		)


class MissingScrobbleParameters(Exception):
	def __init__(self,params=[]):
		self.params = params

class MissingEntityParameter(Exception):
	pass

class EntityDoesNotExist(HTTPError):
	entitytype = 'Entity'
	def __init__(self,entitydict):
		self.entitydict = entitydict
		super().__init__(
			status=404,
			body=f"The {self.entitytype} '{self.entitydict}' does not exist in the database."
		)

class ArtistDoesNotExist(EntityDoesNotExist):
	entitytype = 'Artist'
class AlbumDoesNotExist(EntityDoesNotExist):
	entitytype = 'Album'
class TrackDoesNotExist(EntityDoesNotExist):
	entitytype = 'Track'
