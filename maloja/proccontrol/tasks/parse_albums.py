from doreah.io import col

def parse_albums(strategy=None,prefer_existing=False):

	if strategy not in ("track","none","all","majority","most"):
		print("""
Please specify your album parsing strategy:

    --strategy           Specify what strategy to use when the scrobble contains
                         no information about album artists.
                         track      Take the track artists. This can lead to
                                    separate albums being created for compilation
                                    albums or albums that have collaboration tracks.
                         none       Merge all albums with the same name and assign
                                    'Various Artists' as the album artist.
                         all        Merge all albums with the same name and assign
                                    every artist that appears on the album as an album
                                    artist.
                         majority   Merge all albums with the same name and assign
                                    artists that appear in at least half the tracks
                                    of the album as album artists. [RECOMMENDED]
                         most       Merge all albums with the same name and assign
                                    the artist that appears most on the album as album
                                    artist.
    --prefer_existing    If an album with the same name already exists, use it
                         without further examination of track artists.
		""")
		return



	from ...database.sqldb import guess_albums, get_album_id, add_track_to_album

	print("Parsing album information...")
	result = guess_albums()

	result = {track_id:result[track_id] for track_id in result if result[track_id]["assigned"]}
	print("Found",col['yellow'](len(result)),"Tracks to assign albums to")

	result_authorative = {track_id:result[track_id] for track_id in result if result[track_id]["assigned"]["artists"]}
	result_guesswork = {track_id:result[track_id] for track_id in result if not result[track_id]["assigned"]["artists"]}

	i = 0

	def countup(i):
		i+=1
		if (i % 100) == 0:
			print(f"Added album information for {i} of {len(result)} tracks...")
		return i

	for track_id in result_authorative:
		albuminfo = result[track_id]['assigned']
		album_id = get_album_id(albuminfo)
		add_track_to_album(track_id,album_id)
		i=countup(i)

	albums = {}
	for track_id in result_guesswork:
		albuminfo = result[track_id]['assigned']

		# check if already exists
		if prefer_existing:
			album_id = get_album_id(albuminfo,ignore_albumartists=True,create_new=False)
			if album_id:
				add_track_to_album(track_id,album_id)
				i=countup(i)
				continue

		if strategy == 'track':
			albuminfo['artists'] = result[track_id]['guess_artists']
			album_id = get_album_id(albuminfo)
			add_track_to_album(track_id,album_id)
			i=countup(i)
			continue

		if strategy == 'none':
			albuminfo['artists'] = []
			album_id = get_album_id(albuminfo)
			add_track_to_album(track_id,album_id)
			i=countup(i)
			continue

		if strategy in ['all','majority','most']:
			cleantitle = albuminfo['albumtitle'].lower()
			albums.setdefault(cleantitle,{'track_ids':[],'artists':{},'title':albuminfo['albumtitle']})
			albums[cleantitle]['track_ids'].append(track_id)
			for a in result[track_id]['guess_artists']:
				albums[cleantitle]['artists'].setdefault(a,0)
				albums[cleantitle]['artists'][a] += 1


	for cleantitle in albums:
		artistoptions = albums[cleantitle]['artists']
		track_ids = albums[cleantitle]['track_ids']
		realtitle = albums[cleantitle]['title']
		if strategy == 'all':
			artists = [a for a in artistoptions]
		elif strategy == 'majority':
			artists = [a for a in artistoptions if artistoptions[a] >= (len(track_ids) / 2)]
		elif strategy == 'most':
			artists = [max(artistoptions,key=artistoptions.get)]

		for track_id in track_ids:
			album_id = get_album_id({'albumtitle':realtitle,'artists':artists})
			add_track_to_album(track_id,album_id)
			i=countup(i)

	print(col['lawngreen']("Done!"))
