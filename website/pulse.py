import urllib
import database

		
def instructions(keys):
	from utilities import getArtistImage, getTrackImage
	from htmlgenerators import artistLink, artistLinks, trackLink, scrobblesLink, keysToUrl, KeySplit
	from htmlmodules import module_pulse	
	from malojatime import range_desc, delimit_desc
	
	filterkeys, timekeys, delimitkeys, _ = KeySplit(keys)
	
	
	# describe the scope (and creating a key for the relevant artist or track)
	limitstring = ""
	#limitkey = {}
	if filterkeys.get("track") is not None:
		#limitkey["track"] = {"artists":keys.getall("artist"),"title":keys.get("title")}
		limitstring += "of " + trackLink(filterkeys["track"]) + " "
		limitstring += "by " + artistLinks(filterkeys["track"]["artists"])
	
	elif filterkeys.get("artist") is not None:
		#limitkey["artist"], limitkey["associated"] = keys.get("artist"), (keys.get("associated")!=None)
		limitstring += "of " + artistLink(filterkeys.get("artist"))
		if filterkeys.get("associated"):
			data = database.artistInfo(filterkeys["artist"])
			moreartists = data["associated"]
			if moreartists != []:
				limitstring += " <span class='extra'>including " + artistLinks(moreartists) + "</span>"
				
	limitstring += " " + range_desc(**timekeys)
	
	delimitstring = delimit_desc(**delimitkeys)
		
	
	# get image	
	if filterkeys.get("track") is not None:
		imgurl = getTrackImage(filterkeys.get("track")["artists"],filterkeys.get("track")["title"])
	elif filterkeys.get("artist") is not None:
		imgurl = getArtistImage(keys.get("artist"))
	else:
		imgurl = ""
		
	pushresources = [{"file":imgurl,"type":"image"}] if imgurl.startswith("/") else []
	

	
	html_pulse = module_pulse(**filterkeys,**timekeys,**delimitkeys)
	
	replace = {"KEY_PULSE_TABLE":html_pulse,"KEY_IMAGEURL":imgurl,"KEY_LIMITS":limitstring,"KEY_PULSEDETAILS":delimitstring}
	
	return (replace,pushresources)
		
