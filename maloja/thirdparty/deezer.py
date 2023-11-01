from . import MetadataInterface, RateLimitExceeded


class Deezer(MetadataInterface):
	name = "Deezer"
	identifier = "deezer"

	settings = {
	}

	metadata = {
		#"trackurl": "https://api.deezer.com/search?q={artist}%20{title}",
		"artisturl": "https://api.deezer.com/search?q={artist}",
		"albumurl": "https://api.deezer.com/search?q={artist}%20{title}",
		"response_type":"json",
		#"response_parse_tree_track": ["data",0,"album","cover_medium"],
		"response_parse_tree_artist": ["data",0,"artist","picture_medium"],
		"response_parse_tree_album": ["data",0,"album","cover_medium"],
		"required_settings": [],
		"enabled_entity_types": ["artist","album"]
	}

	delay = 1

	def get_image_track(self,track):
		return None
		# we can use the album pic from the track search,
		# but should do so via maloja logic


	def handle_json_result_error(self,result):
		if result.get('data') == []:
			return True
		if result.get('error',{}).get('code',None) == 4:
			self.delay += 1
			# this is permanent (for the lifetime of the process)
			# but that's actually ok
			# since hitting the rate limit means we are doing this too fast
			# and these requests arent really time sensitive
			raise RateLimitExceeded()
