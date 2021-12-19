import os
from doreah.settings import get_settings
from doreah.settings import config as settingsconfig
from doreah.configuration import Configuration
from doreah.configuration import types as tp

pthj = os.path.join


# if DATA_DIRECTORY is specified, this is the directory to use for EVERYTHING, no matter what
# but with asynnetrical structure, cache and logs in subfolders
# otherwise, each directory is treated seperately
# in that case, individual settings for each are respected
# DIRECRORY_CONFIG, DIRECRORY_STATE, DIRECTORY_LOGS and DIRECTORY_CACHE
# config can only be determined by environment variable, the others can be loaded
# from the config files
# explicit settings will always be respected. if there are none:
# first check if there is any indication of one of the possibilities being populated already
# if not, use the first we have permissions for
# after we decide which to use, fix it in settings to avoid future heuristics

try:
	HOME_DIR = os.environ["XDG_DATA_HOME"].split(":")[0]
	assert os.path.exists(HOME_DIR)
except:
	HOME_DIR = os.path.join(os.environ["HOME"],".local/share/")
usrfol = pthj(HOME_DIR,"maloja")
etccfg = '/etc/maloja'
varlib = '/var/lib/maloja'
varcac = '/var/cache/maloja'
varlog = '/var/log/maloja'

dir_settings = {
	"config":None,
	"state":None,
	"logs":None,
	"cache":None,
#	"clients":None,
#	"rules":None,
#	"settings":None,
#	"auth":None,
#	"backups":None,
#	"images":None,
#	"scrobbles":None,
#	"logs":None,
#	"cache":None
}

dir_options = {
	"config":[
		"/etc/maloja",
		usrfol
	],
	"state":[
		"/var/lib/maloja",
		"/etc/maloja",
		usrfol
	],
	"logs":[
		"/var/log/maloja",
		"/etc/maloja/logs",
		pthj(usrfol,"logs")
	],
	"cache":[
		"/var/cache/maloja",
		"/etc/maloja/cache",
		pthj(usrfol,"cache")
	]
}

sentinels = {
	"config":"settings",
	"state":"scrobbles",
	"logs":None,
	"cache":None,
}

# check environ variables
stng_data = get_settings("DATA_DIRECTORY",files=[],environ_prefix="MALOJA_")
if stng_data is not None:
	dir_settings['config'] = stng_data
	dir_settings['state'] = stng_data
	dir_settings['cache'] = pthj(stng_data,'cache')
	dir_settings['logs'] = pthj(stng_data,'logs')
else:
	dir_settings['config'], dir_settings['state'], dir_settings['cache'], dir_settings['logs'] = get_settings("DIRECTORY_CONFIG","DIRECTORY_STATE","DIRECTORY_LOGS","DIRECTORY_CACHE",files=[],environ_prefix="MALOJA_")
	# as soon as we know the config directory, we can load from settings file
	if dir_settings['config'] is not None:
		settingsfiles = [pthj(dir_settings['config'],'settings','default.ini'),pthj(dir_settings['config'],'settings','settings.ini')]
		dir_settings['config'], dir_settings['state'], dir_settings['cache'], dir_settings['logs'] = get_settings("DIRECTORY_CONFIG","DIRECTORY_STATE","DIRECTORY_LOGS","DIRECTORY_CACHE",files=settingsfiles,environ_prefix="MALOJA_")


# now to the stuff no setting has explicitly defined
for dirtype in dir_settings:
	if dir_settings[dirtype] is None:
		for option in dir_options[dirtype]:
			if os.path.exists(option):
				# check if this is really the directory used for this category (/etc/maloja could be used for state or just config)
				if sentinels[dirtype] is None or os.path.exists(pthj(option,sentinels[dirtype])):
					dir_settings[dirtype] = option
					break

# if no directory seems to exist, use the first writable one
for dirtype in dir_settings:
	if dir_settings[dirtype] is None:
		for option in dir_options[dirtype]:
			try:
				os.makedirs(option,exist_ok=True)
				os.mknod(pthj(option,".test"))
				os.remove(pthj(option,".test"))
				dir_settings[dirtype] = option
				break
			except:
				pass


assert all((dir_settings[s] is not None) for s in dir_settings)


data_directories = {
	"auth":pthj(dir_settings['state'],"auth"),
	"backups":pthj(dir_settings['state'],"backups"),
	"images":pthj(dir_settings['state'],"images"),
	"scrobbles":pthj(dir_settings['state'],"scrobbles"),
	"rules":pthj(dir_settings['config'],"rules"),
	"clients":pthj(dir_settings['config'],"clients"),
	"settings":pthj(dir_settings['config'],"settings"),
	"css":pthj(dir_settings['config'],"custom_css"),
	"logs":pthj(dir_settings['logs']),
	"cache":pthj(dir_settings['cache']),
}


data_dir = {
	k:lambda *x,k=k: pthj(data_directories[k],*x)  for k in data_directories
}





### DOREAH CONFIGURATION

from doreah import config

config(
	settings={
		"files":[
			data_dir['settings']("default.ini"),
			data_dir['settings']("settings.ini")
		],
		"environ_prefix":"MALOJA_"
	},
	caching={
		"folder": data_dir['cache']()
	},
	auth={
		"multiuser":False,
		"cookieprefix":"maloja",
		"stylesheets":["/style.css"],
		"dbfile":data_dir['auth']("auth.ddb")
	}
)

# because we loaded a doreah module already before setting the config, we need to to that manually
settingsconfig._readpreconfig()

config(
	logging={
		"logfolder": data_dir['logs']() if get_settings("LOGGING") else None
	},
	regular={
		"autostart": False,
		"offset": get_settings("TIMEZONE")
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








# new config


malojaconfig = Configuration(
		settings={
			"Setup":{
				"data_directory":(tp.String(),										"Data Directory",				None,					"Folder for all user data. Overwrites all choices for specific directories."),
				"directory_config":(tp.String(),									"Config Directory",				"/etc/maloja",			"Folder for config data. Only applied when global data directory is not set."),
				"directory_state":(tp.String(),										"State Directory",				"/var/lib/maloja",		"Folder for state data. Only applied when global data directory is not set."),
				"directory_logs":(tp.String(),										"Log Directory",				"/var/log/maloja",		"Folder for log data. Only applied when global data directory is not set."),
				"directory_cache":(tp.String(),										"Cache Directory",				"/var/cache/maloja",	"Folder for cache data. Only applied when global data directory is not set."),
				"skip_setup":(tp.Boolean(),											"Skip Setup",					False,					"Make server setup process non-interactive"),
				"force_password":(tp.String(),										"Force Password",				None,					"On startup, overwrite admin password with this one"),
				"clean_output":(tp.Boolean(),										"Avoid Mutable Console Output",	False,					"No console output that will cause problems when piped to other outputs")
			},
			"Debug":{
				"logging":(tp.Boolean(),											"Enable Logging",				True),
				"dev_mode":(tp.Boolean(),											"Enable developer mode",		False),
			},
			"Network":{
				"host":(tp.String(),												"Host",							"::",					"Use :: for default IPv6, 0.0.0.0 for default IPv4"),
				"port":(tp.Integer(),												"Port",							42010),
			},
			"Technical":{
				"cache_expire_positive":(tp.Integer(),								"Days until images are refetched", 					300),
				"cache_expire_negative":(tp.Integer(),								"Days until failed image fetches are reattempted",	30),
				"use_db_cache":(tp.Boolean(),										"Use DB Cache",										True),
				"cache_database_short":(tp.Boolean(),								"Use volatile Database Cache",						True),
				"cache_database_perm":(tp.Boolean(),								"Use permanent Database Cache",						True),
				"db_cache_entries":(tp.Integer(),									"Maximal Cache entries",							10000),
				"db_max_memory":(tp.Integer(max=100,min=20),						"RAM Percentage Theshold",							75)
			},
			"Fluff":{
				"scrobbles_gold":(tp.Integer(),										"Scrobbles for Gold",			250),
				"scrobbles_platinum":(tp.Integer(),									"Scrobbles for Platinum",		500),
				"scrobbles_diamond":(tp.Integer(),									"Scrobbles for Diamond",		1000),
				"name":(tp.String(),												"Name",							"Maloja User")
			},
			"Third Party Services":{
				"metadata_providers":(tp.List(tp.String()),							"Metadata Providers",			['lastfm','spotify','deezer','musicbrainz']),
				"scrobble_lastfm":(tp.Boolean(),									"Proxy-Scrobble to Last.fm",	False),
				"lastfm_api_key":(tp.String(),										"Last.fm API Key",				None),
				"lastfm_api_secret":(tp.String(),									"Last.fm API Secret",			None),
				"spotify_api_id":(tp.String(),										"Spotify API ID",				None),
				"spotify_api_secret":(tp.String(),									"Spotify API Secret",			None),
				"lastfm_api_key":(tp.String(),										"Last.fm API Key",				None),
				"audiodb_api_key":(tp.String(),										"TheAudioDB API Key",			None),
				"track_search_provider":(tp.String(),								"Track Search Provider",		None),
				"send_stats":(tp.Boolean(),											"Send Statistics",				None),

			},
			"Database":{
				"invalid_artists":(tp.Set(tp.String()),								"Invalid Artists",				["[Unknown Artist]","Unknown Artist","Spotify"]),
				"remove_from_title":(tp.Set(tp.String()),							"Remove from Title",			["(Original Mix)","(Radio Edit)","(Album Version)","(Explicit Version)","(Bonus Track)"]),
				"delimiters_feat":(tp.Set(tp.String()),								"Featuring Delimiters",			["ft.","ft","feat.","feat","featuring","Ft.","Ft","Feat.","Feat","Featuring"]),
				"delimiters_informal":(tp.Set(tp.String()),							"Informal Delimiters",			["vs.","vs","&"]),
				"delimiters_formal":(tp.Set(tp.String()),							"Formal Delimiters",			[";","/"])
			},
			"Web Interface":{
				"default_range_charts_artists":(tp.Choice({'alltime':'All Time','year':'Year','month':"Month",'week':'Week'}),	"Default Range Artist Charts",	"year"),
				"default_range_charts_tracks":(tp.Choice({'alltime':'All Time','year':'Year','month':"Month",'week':'Week'}),	"Default Range Track Charts",	"year"),
				"default_step_pulse":(tp.Choice({'year':'Year','month':"Month",'week':'Week','day':'Day'}),						"Default Pulse Step",			"month"),
				"charts_display_tiles":(tp.Boolean(),								"Display Chart Tiles",			False),
				"discourage_cpu_heavy_stats":(tp.Boolean(),							"Discourage CPU-heavy stats",	False),
				"use_local_images":(tp.Boolean(),									"Use Local Images",				True),
				"local_image_rotate":(tp.Integer(),									"Local Image Rotate",			3600),
				"timezone":(tp.Integer(),											"UTC Offset",					0),
				"time_format":(tp.String(),											"Time Format",					"%d. %b %Y %I:%M %p")
			}
		},
		configfile=data_dir['settings']("settings.ini"),
		save_endpoint="/apis/mlj_1/settings"

	)
