import urllib
import database

		
def instructions(keys):
	from utilities import getArtistImage, getTrackImage
	from htmlgenerators import artistLink, artistLinks, trackLink, KeySplit
	from htmlmodules import module_scrobblelist	
	from malojatime import range_desc
	
	
	filterkeys, timekeys, _, amountkeys = KeySplit(keys)
	
	# describe the scope
	limitstring = ""
	if filterkeys.get("track") is not None:
		limitstring += "of " + trackLink(filterkeys["track"]) + " "
		limitstring += "by " + artistLinks(filterkeys["track"]["artists"])
	
	elif filterkeys.get("artist") is not None:
		limitstring += "by " + artistLink(filterkeys.get("artist"))
		if filterkeys.get("associated"):
			data = database.artistInfo(filterkeys["artist"])
			moreartists = data.get("associated")
			if moreartists != []:
				limitstring += " <span class='extra'>including " + artistLinks(moreartists) + "</span>"
		
	limitstring += " " + range_desc(**timekeys)

	
	html, amount, rep = module_scrobblelist(**filterkeys,**timekeys,**amountkeys)
	
	# get image	
	if filterkeys.get("track") is not None:
		imgurl = getTrackImage(filterkeys.get("track")["artists"],filterkeys.get("track")["title"],fast=True)
	elif filterkeys.get("artist") is not None:
		imgurl = getArtistImage(keys.get("artist"),fast=True)
	elif rep is not None:
		imgurl = getTrackImage(rep["artists"],rep["title"],fast=True)
	else:
		imgurl = ""
	
		
	pushresources = [{"file":imgurl,"type":"image"}] if imgurl.startswith("/") else []

	
	replace = {"KEY_SCROBBLELIST":html,"KEY_SCROBBLES":str(amount),"KEY_IMAGEURL":imgurl,"KEY_LIMITS":limitstring}
	
	return (replace,pushresources)
		
