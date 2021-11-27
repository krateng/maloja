from . import MetadataInterface

class Deezer(MetadataInterface):
	name = "Deezer"
	identifier = "deezer"

	settings = {
	}

	metadata = {
		"trackurl": "https://api.deezer.com/search?q={artist}%20{title}",
		"artisturl": "https://api.deezer.com/search?q={artist}",
		"response_type":"json",
		"response_parse_tree_track": ["data",0,"album","cover_medium"],
		"response_parse_tree_artist": ["data",0,"artist","picture_medium"],
		"required_settings": [],
	}
