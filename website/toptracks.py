import urllib

		
def instructions(keys):
	from utilities import getArtistInfo, getTrackInfo
	from htmlgenerators import artistLink, KeySplit
	from htmlmodules import module_trackcharts
	
	filterkeys, timekeys, _, amountkeys = KeySplit(keys)
	

	limitstring = ""

	
	html_charts, rep = module_trackcharts(**amountkeys,**timekeys,**filterkeys)
	
	
	if filterkeys.get("artist") is not None:
		imgurl = getArtistInfo(filterkeys.get("artist")).get("image")
		limitstring = "by " + artistLink(filterkeys.get("artist"))
	elif rep is not None:
		imgurl = getTrackInfo(rep["artists"],rep["title"]).get("image")		
	else:
		imgurl = ""
	
	pushresources = [{"file":imgurl,"type":"image"}] if imgurl.startswith("/") else []
	


	replace = {"KEY_TOPARTIST_IMAGEURL":imgurl,"KEY_TRACKLIST":html_charts,"KEY_LIMITS":limitstring}
	
	return (replace,pushresources)

