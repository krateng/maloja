# for information that is not authorative, but should be saved anyway because it
# changes infrequently and DB access is expensive

from doreah.regular import runyearly, rundaily
from .. import database
from . import sqldb
from .. import malojatime as mjt



medals_artists = {
	# year: {'gold':[],'silver':[],'bronze':[]}
}
medals_tracks = {
	# year: {'gold':[],'silver':[],'bronze':[]}
}
medals_albums = {
	# year: {'gold':[],'silver':[],'bronze':[]}
}

weekly_topartists = []
weekly_toptracks = []
weekly_topalbums = []

@runyearly
def update_medals():

	global medals_artists, medals_tracks, medals_albums
	medals_artists.clear()
	medals_tracks.clear()
	medals_albums.clear()

	with sqldb.engine.begin() as conn:
		for year in mjt.ranges(step="year"):
			if year == mjt.thisyear(): break

			charts_artists = sqldb.count_scrobbles_by_artist(since=year.first_stamp(),to=year.last_stamp(),resolve_ids=False,dbconn=conn)
			charts_tracks = sqldb.count_scrobbles_by_track(since=year.first_stamp(),to=year.last_stamp(),resolve_ids=False,dbconn=conn)
			charts_albums = sqldb.count_scrobbles_by_album(since=year.first_stamp(),to=year.last_stamp(),resolve_ids=False,dbconn=conn)

			entry_artists = {'gold':[],'silver':[],'bronze':[]}
			entry_tracks = {'gold':[],'silver':[],'bronze':[]}
			entry_albums = {'gold':[],'silver':[],'bronze':[]}
			medals_artists[year.desc()] = entry_artists
			medals_tracks[year.desc()] = entry_tracks
			medals_albums[year.desc()] = entry_albums

			for entry in charts_artists:
				if entry['rank'] == 1: entry_artists['gold'].append(entry['artist_id'])
				elif entry['rank'] == 2: entry_artists['silver'].append(entry['artist_id'])
				elif entry['rank'] == 3: entry_artists['bronze'].append(entry['artist_id'])
				else: break
			for entry in charts_tracks:
				if entry['rank'] == 1: entry_tracks['gold'].append(entry['track_id'])
				elif entry['rank'] == 2: entry_tracks['silver'].append(entry['track_id'])
				elif entry['rank'] == 3: entry_tracks['bronze'].append(entry['track_id'])
				else: break
			for entry in charts_albums:
				if entry['rank'] == 1: entry_albums['gold'].append(entry['album_id'])
				elif entry['rank'] == 2: entry_albums['silver'].append(entry['album_id'])
				elif entry['rank'] == 3: entry_albums['bronze'].append(entry['album_id'])
				else: break




@rundaily
def update_weekly():

	global weekly_topartists, weekly_toptracks, weekly_topalbums
	weekly_topartists.clear()
	weekly_toptracks.clear()
	weekly_topalbums.clear()

	with sqldb.engine.begin() as conn:
		for week in mjt.ranges(step="week"):
			if week == mjt.thisweek(): break


			charts_artists = sqldb.count_scrobbles_by_artist(since=week.first_stamp(),to=week.last_stamp(),resolve_ids=False,dbconn=conn)
			charts_tracks = sqldb.count_scrobbles_by_track(since=week.first_stamp(),to=week.last_stamp(),resolve_ids=False,dbconn=conn)
			charts_albums = sqldb.count_scrobbles_by_album(since=week.first_stamp(),to=week.last_stamp(),resolve_ids=False,dbconn=conn)

			for entry in charts_artists:
				if entry['rank'] == 1: weekly_topartists.append(entry['artist_id'])
				else: break
			for entry in charts_tracks:
				if entry['rank'] == 1: weekly_toptracks.append(entry['track_id'])
				else: break
			for entry in charts_albums:
				if entry['rank'] == 1: weekly_topalbums.append(entry['album_id'])
				else: break
