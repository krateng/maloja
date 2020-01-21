from doreah.settings import get_settings, update_settings
import urllib.request
import hashlib
import xml.etree.ElementTree as ET
from bottle import redirect, request
from ..database import checkAPIkey
from ..external import lfmbuild

def instructions(keys):
	authenticated = False
	if "Cookie" in request.headers:
		cookies = request.headers["Cookie"].split(";")
		for c in cookies:
			if c.strip().startswith("apikey="):
				authenticated = checkAPIkey(c.strip()[7:])

	if "token" in keys and authenticated:
		token = keys.get("token")
		parameters = {
			"method":"auth.getSession",
			"token":token,
			"api_key":get_settings("LASTFM_API_KEY")
		}
		response = urllib.request.urlopen("http://ws.audioscrobbler.com/2.0/?" + lfmbuild(parameters))
		xml = response.read()
		data = ET.fromstring(xml)
		if data.attrib.get("status") == "ok":
			username = data.find("session").find("name").text
			sessionkey = data.find("session").find("key").text

			update_settings("settings/settings.ini",{"LASTFM_API_SK":sessionkey,"LASTFM_USERNAME":username},create_new=True)

		return "/proxy"

	else:
		key,secret,sessionkey,name = get_settings("LASTFM_API_KEY","LASTFM_API_SECRET","LASTFM_API_SK","LASTFM_USERNAME")

		if key is None:
			lastfm = "<td>No Last.fm key provided</td>"
		elif secret is None:
			lastfm = "<td>No Last.fm secret provided</td>"
		elif sessionkey is None and authenticated:
			url = "http://www.last.fm/api/auth/?api_key=" + key + "&cb="
			lastfm = "<td class='button'><a id='lastfmlink' href='" + url + "'><div>Connect</div></a></td>"
		elif sessionkey is None:
			lastfm = "<td>Not active</td>"
		else:

			lastfm = "<td>Account: " + name + "</td>"



	return {"KEY_STATUS_LASTFM":lastfm},[]
