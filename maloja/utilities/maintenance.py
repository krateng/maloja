from ..__pkginfo__ import version

from doreah.regular import yearly, daily
from doreah import settings
from doreah.logging import log

import datetime
import json
import urllib
import itertools



get_track = lambda x:(frozenset(x["track"]["artists"]),x["track"]["title"])
get_artist = lambda x:x["artist"]

def group_by_attribute(sequence,attribute):
	grouped = itertools.groupby(sequence,key=lambda x:x[attribute])
	for attrvalue,members in grouped:
		yield attrvalue,list(members)

def collect_rankings(chart,identify,collection,iteration=None,count=True):
	grouped = group_by_attribute(chart,"rank")
	for rank, members in grouped:
		if not count and rank not in rankmedals: break
		if count and rank != 1: break

		for m in members:
			# get the actual object that we're counting
			entity = identify(m)

			# count no1 spots
			if count:
				collection[entity] = collection.setdefault(entity,0) + 1

			# collect instances of top3 spots
			else:
				medal = rankmedals[rank]
				collection.setdefault(entity,{}).setdefault(medal,[]).append(iteration)


rankmedals = {
	1:'gold',
	2:'silver',
	3:'bronze'
}

@yearly
def update_medals():


	from ..database import MEDALS, MEDALS_TRACKS, STAMPS, get_charts_artists, get_charts_tracks

	currentyear = datetime.datetime.utcnow().year
	try:
		firstyear = datetime.datetime.utcfromtimestamp(STAMPS[0]).year
	except:
		firstyear = currentyear


	MEDALS.clear()
	MEDALS_TRACKS.clear()

	for year in range(firstyear,currentyear):
		charts_artists = get_charts_artists(within=[year])
		charts_tracks = get_charts_tracks(within=[year])

		collect_rankings(charts_artists,get_artist,MEDALS,iteration=year,count=False)
		collect_rankings(charts_tracks,get_track,MEDALS_TRACKS,iteration=year,count=False)


@daily
def update_weekly():

	from ..database import WEEKLY_TOPTRACKS, WEEKLY_TOPARTISTS, get_charts_artists, get_charts_tracks
	from ..malojatime import ranges, thisweek


	WEEKLY_TOPARTISTS.clear()
	WEEKLY_TOPTRACKS.clear()

	for week in ranges(step="week"):
		if week == thisweek(): break

		charts_artists = get_charts_artists(timerange=week)
		charts_tracks = get_charts_tracks(timerange=week)

		collect_rankings(charts_artists,get_artist,WEEKLY_TOPARTISTS)
		collect_rankings(charts_tracks,get_track,WEEKLY_TOPTRACKS)


@daily
def send_stats():
	if settings.get_settings("SEND_STATS"):

		log("Sending daily stats report...")

		from ..database import ARTISTS, TRACKS, SCROBBLES

		keys = {
			"url":"https://myrcella.krateng.ch/malojastats",
			"method":"POST",
			"headers":{"Content-Type": "application/json"},
			"data":json.dumps({
				"name":settings.get_settings("NAME"),
				"url":settings.get_settings("PUBLIC_URL"),
				"version":".".join(str(d) for d in version),
				"artists":len(ARTISTS),
				"tracks":len(TRACKS),
				"scrobbles":len(SCROBBLES)
			}).encode("utf-8")
		}
		try:
			req = urllib.request.Request(**keys)
			response = urllib.request.urlopen(req)
			log("Sent daily report!")
		except:
			log("Could not send daily report!")
