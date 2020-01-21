import urllib
from .. import database
import json
from ..htmlgenerators import artistLink
from ..utilities import getArtistImage


def instructions(keys):

	compareto = keys.get("to")
	compareurl = compareto + "/api/info"

	response = urllib.request.urlopen(compareurl)
	strangerinfo = json.loads(response.read())

	owninfo = database.info()

	database.add_known_server(compareto)

	artists = {}

	for a in owninfo["artists"]:
		artists[a.lower()] = {"name":a,"self":int(owninfo["artists"][a]*1000),"other":0}

	for a in strangerinfo["artists"]:
		artists[a.lower()] = artists.setdefault(a.lower(),{"name":a,"self":0})
		artists[a.lower()]["other"] = int(strangerinfo["artists"][a]*1000)

	for a in artists:
		common = min(artists[a]["self"],artists[a]["other"])
		artists[a]["self"] -= common
		artists[a]["other"] -= common
		artists[a]["common"] = common

	best = sorted((artists[a]["name"] for a in artists),key=lambda x: artists[x.lower()]["common"],reverse=True)

	result = {
		"unique_self":sum(artists[a]["self"] for a in artists if artists[a]["common"] == 0),
		"more_self":sum(artists[a]["self"] for a in artists if artists[a]["common"] != 0),
	#	"common":{
	#		**{
	#			artists[a]["name"]:artists[a]["common"]
	#		for a in best[:3]},
	#	None: sum(artists[a]["common"] for a in artists if a not in best[:3])
	#	},
		"common":sum(artists[a]["common"] for a in artists),
		"more_other":sum(artists[a]["other"] for a in artists if artists[a]["common"] != 0),
		"unique_other":sum(artists[a]["other"] for a in artists if artists[a]["common"] == 0)
	}

	total = sum(result[c] for c in result)

	percentages = {c:result[c]*100/total for c in result}
	css = []

	cumulative = 0
	for color,category in [
		("rgba(255,255,255,0.2)","unique_self"),
		("rgba(255,255,255,0.5)","more_self"),
		("white","common"),
		("rgba(255,255,255,0.5)","more_other"),
		("rgba(255,255,255,0.2)","unique_other")]:
		cumulative += percentages[category]
		css.append(color + " " + str(cumulative) + "%")


	fullmatch = percentages["common"]
	partialmatch = percentages["more_self"] + percentages["more_other"]

	match = fullmatch + (partialmatch)/2
	pixel_fullmatch = fullmatch * 2.5
	pixel_partialmatch = (fullmatch+partialmatch) * 2.5

	match = min(match,100)


	matchcolor = format(int(min(1,match/50)*255),"02x") * 2 + format(int(max(0,match/50-1)*255),"02x")


	return {
		"KEY_CIRCLE_CSS":",".join(css),
		"KEY_CICLE_COLOR":matchcolor,
		"KEY_MATCH":str(round(match,2)),
		"KEY_FULLMATCH":str(int(pixel_fullmatch)),
		"KEY_PARTIALMATCH":str(int(pixel_partialmatch)),
		"KEY_NAME_SELF":owninfo["name"],
		"KEY_NAME_OTHER":strangerinfo["name"],
		"KEY_BESTARTIST_LINK":artistLink(best[0]),
		"KEY_BESTARTIST_IMAGE":getArtistImage(best[0])
	},[]
