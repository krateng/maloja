class EntityExists(Exception):
	def __init__(self,entitydict):
		self.entitydict = entitydict


class TrackExists(EntityExists):
	pass

class ArtistExists(EntityExists):
	pass
