from ..__pkginfo__ import version

from doreah.regular import yearly, daily
from doreah import settings
from doreah.logging import log

import datetime
import json
import urllib

@yearly
def update_medals():


	from ..database import MEDALS, MEDALS_TRACKS, STAMPS, get_charts_artists, get_charts_tracks

	currentyear = datetime.datetime.utcnow().year
	try:
		firstyear = datetime.datetime.utcfromtimestamp(STAMPS[0]).year
	except:
		firstyear = currentyear


	MEDALS.clear()
	for year in range(firstyear,currentyear):

		charts = get_charts_artists(within=[year])
		for a in charts:

			artist = a["artist"]
			if a["rank"] == 1: MEDALS.setdefault(artist,{}).setdefault("gold",[]).append(year)
			elif a["rank"] == 2: MEDALS.setdefault(artist,{}).setdefault("silver",[]).append(year)
			elif a["rank"] == 3: MEDALS.setdefault(artist,{}).setdefault("bronze",[]).append(year)
			else: break

	MEDALS_TRACKS.clear()
	for year in range(firstyear,currentyear):

		charts = get_charts_tracks(within=[year])
		for t in charts:

			track = (frozenset(t["track"]["artists"]),t["track"]["title"])
			if t["rank"] == 1: MEDALS_TRACKS.setdefault(track,{}).setdefault("gold",[]).append(year)
			elif t["rank"] == 2: MEDALS_TRACKS.setdefault(track,{}).setdefault("silver",[]).append(year)
			elif t["rank"] == 3: MEDALS_TRACKS.setdefault(track,{}).setdefault("bronze",[]).append(year)
			else: break

@daily
def update_weekly():

	from ..database import WEEKLY_TOPTRACKS, WEEKLY_TOPARTISTS, get_charts_artists, get_charts_tracks
	from ..malojatime import ranges, thisweek


	WEEKLY_TOPARTISTS.clear()
	WEEKLY_TOPTRACKS.clear()

	for week in ranges(step="week"):
		if week == thisweek(): break
		for a in get_charts_artists(timerange=week):
			artist = a["artist"]
			if a["rank"] == 1: WEEKLY_TOPARTISTS[artist] = WEEKLY_TOPARTISTS.setdefault(artist,0) + 1

		for t in get_charts_tracks(timerange=week):
			track = (frozenset(t["track"]["artists"]),t["track"]["title"])
			if t["rank"] == 1: WEEKLY_TOPTRACKS[track] = WEEKLY_TOPTRACKS.setdefault(track,0) + 1


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
