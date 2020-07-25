import os
from doreah.settings import get_settings
from doreah.settings import config as settingsconfig



# check environment variables for data directory
# otherwise, go with defaults
setting_datadir = get_settings("DATA_DIRECTORY",files=[],environ_prefix="MALOJA_")
if setting_datadir is not None and os.path.exists(setting_datadir):
	DATA_DIR = setting_datadir
else:
	try:
		HOME_DIR = os.environ["XDG_DATA_HOME"].split(":")[0]
		assert os.path.exists(HOME_DIR)
	except:
		HOME_DIR = os.path.join(os.environ["HOME"],".local/share/")

	DATA_DIR = os.path.join(HOME_DIR,"maloja")

os.makedirs(DATA_DIR,exist_ok=True)



def datadir(*args):
	return os.path.join(DATA_DIR,*args)





### DOREAH CONFIGURATION

from doreah import config

config(
	pyhp={
		"version": 2
	},
	settings={
		"files":[
			datadir("settings/default.ini"),
			datadir("settings/settings.ini")
		],
		"environ_prefix":"MALOJA_"
	},
	caching={
		"folder": datadir("cache")
	},
	regular={
		"autostart": False
	}
)

# because we loaded a doreah module already before setting the config, we need to to that manually
settingsconfig._readpreconfig()

config(
	logging={
		"logfolder": datadir("logs") if get_settings("LOGGING") else None
	}
)

settingsconfig._readpreconfig()



# thumbor

THUMBOR_SERVER, THUMBOR_SECRET = get_settings("THUMBOR_SERVER","THUMBOR_SECRET")
try:
	USE_THUMBOR = THUMBOR_SERVER is not None and THUMBOR_SECRET is not None
	if USE_THUMBOR:
		from libthumbor import CryptoURL
		THUMBOR_GENERATOR = CryptoURL(key=THUMBOR_SECRET)
		OWNURL = get_settings("PUBLIC_URL")
		assert OWNURL is not None
except:
	USE_THUMBOR = False
	log("Thumbor could not be initialized. Is libthumbor installed?")
