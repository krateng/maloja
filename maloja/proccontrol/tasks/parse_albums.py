


def parse_albums(replace=False):

	from ...database import set_aux_mode
	set_aux_mode()

	from ...database.sqldb import guess_albums, get_album_id, add_track_to_album

	print("Parsing album information...")
	result = guess_albums(replace=replace)

	result = {track_id:result[track_id] for track_id in result if result[track_id]["assigned"]}
	print("Adding",len(result),"tracks to albums...")
	i = 0
	for track_id in result:
		album_id = get_album_id(result[track_id]["assigned"])
		add_track_to_album(track_id,album_id)
		i += 1
		if (i % 100) == 0:
			print(i,"of",len(result))
	print("Done!")
