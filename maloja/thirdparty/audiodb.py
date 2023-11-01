from . import MetadataInterface

class AudioDB(MetadataInterface):
	name = "TheAudioDB"
	identifier = "audiodb"

	settings = {
		"api_key":"AUDIODB_API_KEY"
	}

	metadata = {
		#"trackurl": "https://theaudiodb.com/api/v1/json/{api_key}/searchtrack.php?s={artist}&t={title}", #patreon
		"artisturl": "https://www.theaudiodb.com/api/v1/json/{api_key}/search.php?s={artist}",
		#"albumurl": "https://www.theaudiodb.com/api/v1/json/{api_key}/searchalbum.php?s={artist}&a={title}", #patreon
		"response_type":"json",
		#"response_parse_tree_track": ["tracks",0,"astrArtistThumb"],
		"response_parse_tree_artist": ["artists",0,"strArtistThumb"],
		"required_settings": ["api_key"],
		"enabled_entity_types": ["artist"]
	}

	def get_image_track(self,track):
		return None

	def get_image_album(self,album):
		return None
