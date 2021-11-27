from . import MetadataInterface

class AudioDB(MetadataInterface):
	name = "TheAudioDB"
	identifier = "audiodb"

	settings = {
		"api_key":"AUDIODB_API_KEY"
	}

	metadata = {
		#"trackurl": "https://theaudiodb.com/api/v1/json/{api_key}/searchtrack.php?s={artist}&t={title}",
		"artisturl": "https://www.theaudiodb.com/api/v1/json/{api_key}/search.php?s={artist}",
		"response_type":"json",
		#"response_parse_tree_track": ["tracks",0,"astrArtistThumb"],
		"response_parse_tree_artist": ["artists",0,"strArtistThumb"],
		"required_settings": ["api_key"],
	}

	def get_image_track(self,artist):
		return None
