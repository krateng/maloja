import urllib
import database

		
def instructions(keys):
	from utilities import getArtistImage, getTrackImage
	from htmlgenerators import artistLinks, keysToUrl, KeySplit
	from htmlmodules import module_scrobblelist, module_pulse

	
	filterkeys, _, _, _ = KeySplit(keys,forceTrack=True)	
	
	track = filterkeys.get("track")
	imgurl = getTrackImage(track["artists"],track["title"],fast=True)
	pushresources = [{"file":imgurl,"type":"image"}] if imgurl.startswith("/") else []
	
	data = database.trackInfo(track["artists"],track["title"])
	
	scrobblesnum = str(data["scrobbles"])
	pos = "#" + str(data["position"])
	

	html_scrobbles, _, _ = module_scrobblelist(track=track,max_=100,earlystop=True)	 # we have the number already from the trackinfo
	
	html_pulse = module_pulse(track=track,step="year",stepn=1,trail=1)


	replace = {"KEY_TRACKTITLE":track.get("title"),"KEY_ARTISTS":artistLinks(track.get("artists")),"KEY_SCROBBLES":scrobblesnum,"KEY_POSITION":pos,"KEY_IMAGEURL":imgurl,
		"KEY_SCROBBLELINK":keysToUrl(keys),
		"KEY_SCROBBLELIST":html_scrobbles,"KEY_PULSE":html_pulse}
	
	return (replace,pushresources)
