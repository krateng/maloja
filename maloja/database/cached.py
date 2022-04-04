# for information that is not authorative, but should be saved anyway because it
# changes infrequently and DB access is expensive

from doreah.regular import runyearly, rundaily
from .. import database
from .. import malojatime as mjt



medals_artists = {
	# year: {'gold':[],'silver':[],'bronze':[]}
}
medals_tracks = {
	# year: {'gold':[],'silver':[],'bronze':[]}
}

weekly_topartists = []
weekly_toptracks = []

@runyearly
def update_medals():

	global medals_artists, medals_tracks
	medals_artists.clear()
	medals_tracks.clear()

	for year in mjt.ranges(step="year"):
		if year == mjt.thisyear(): break

		charts_artists = database.get_charts_artists(timerange=year)
		charts_tracks = database.get_charts_tracks(timerange=year)

		entry_artists = {'gold':[],'silver':[],'bronze':[]}
		entry_tracks = {'gold':[],'silver':[],'bronze':[]}
		medals_artists[year.desc()] = entry_artists
		medals_tracks[year.desc()] = entry_tracks

		for entry in charts_artists:
			if entry['rank'] == 1: entry_artists['gold'].append(entry['artist'])
			elif entry['rank'] == 2: entry_artists['silver'].append(entry['artist'])
			elif entry['rank'] == 3: entry_artists['bronze'].append(entry['artist'])
			else: break
		for entry in charts_tracks:
			if entry['rank'] == 1: entry_tracks['gold'].append(entry['track'])
			elif entry['rank'] == 2: entry_tracks['silver'].append(entry['track'])
			elif entry['rank'] == 3: entry_tracks['bronze'].append(entry['track'])
			else: break



@rundaily
def update_weekly():

	global weekly_topartists, weekly_toptracks
	weekly_topartists.clear()
	weekly_toptracks.clear()

	for week in mjt.ranges(step="week"):
		if week == mjt.thisweek(): break

		charts_artists = database.get_charts_artists(timerange=week)
		charts_tracks = database.get_charts_tracks(timerange=week)

		for entry in charts_artists:
			if entry['rank'] == 1: weekly_topartists.append(entry['artist'])
			else: break
		for entry in charts_tracks:
			if entry['rank'] == 1: weekly_toptracks.append(entry['track'])
			else: break
