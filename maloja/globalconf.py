import os
from doreah.settings import config as settingsconfig
from doreah.configuration import Configuration
from doreah.configuration import types as tp


# USEFUL FUNCS
pthj = os.path.join

def is_dir_usable(pth):
	try:
		os.makedirs(pth,exist_ok=True)
		os.mknod(pthj(pth,".test"))
		os.remove(pthj(pth,".test"))
		return True
	except:
		return False

def get_env_vars(key,pathsuffix=[]):
	return [pthj(pth,*pathsuffix) for pth in os.environ.get(key,'').split(':') if pth != '']



# get user dirs from environment
user_dirs = {}

user_dirs["home"] = get_env_vars("HOME")
user_dirs["config"] = get_env_vars("XDG_CONFIG_HOME",['maloja'])
user_dirs["cache"] = get_env_vars("XDG_CACHE_HOME",['maloja'])
user_dirs["data"] = get_env_vars("XDG_DATA_HOME",['maloja'])
try:
	user_data_dir = os.environ["XDG_DATA_HOME"].split(":")[0]
	assert os.path.exists(user_data_dir)
except:
	user_data_dir = os.path.join(os.environ["HOME"],".local/share/")
user_data_dir = pthj(user_data_dir,"maloja")

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



### STEP 1 - find out where the settings file is
# environment variables
maloja_dir_config = os.environ.get("MALOJA_DATA_DIRECTORY") or os.environ.get("MALOJA_DIRECTORY_CONFIG")

if maloja_dir_config is None:
	potentialpaths = [
		"/etc/maloja",
		user_data_dir
	]
	# check if it exists anywhere else
	for pth in potentialpaths:
		if os.path.exists(pthj(pth,"settings")):
			maloja_dir_config = pth
			break
	# new installation, pick where to put it
	else:
		# test if we can write to that location
		for pth in potentialpaths:
			if is_dir_usable(pth):
				maloja_dir_config = pth
				break
		else:
			print("Could not find a proper path to put settings file. Please check your permissions!")

oldsettingsfile = pthj(maloja_dir_config,"settings","settings.ini")
newsettingsfile = pthj(maloja_dir_config,"settings.ini")

if os.path.exists(oldsettingsfile):
	os.rename(oldsettingsfile,newsettingsfile)


### STEP 2 - create settings object


malojaconfig = Configuration(
	settings={
		"Setup":{
			"data_directory":(tp.String(),										"Data Directory",				None,					"Folder for all user data. Overwrites all choices for specific directories."),
			"directory_config":(tp.String(),									"Config Directory",				"/etc/maloja",			"Folder for config data. Only applied when global data directory is not set."),
			"directory_state":(tp.String(),										"State Directory",				"/var/lib/maloja",		"Folder for state data. Only applied when global data directory is not set."),
			"directory_logs":(tp.String(),										"Log Directory",				"/var/log/maloja",		"Folder for log data. Only applied when global data directory is not set."),
			"directory_cache":(tp.String(),										"Cache Directory",				"/var/cache/maloja",	"Folder for cache data. Only applied when global data directory is not set."),
			"skip_setup":(tp.Boolean(),											"Skip Setup",					False,					"Make server setup process non-interactive. Vital for Docker."),
			"force_password":(tp.String(),										"Force Password",				None,					"On startup, overwrite admin password with this one. This should usually only be done via environment variable in Docker."),
			"clean_output":(tp.Boolean(),										"Avoid Mutable Console Output",	False,					"Use if console output will be redirected e.g. to a web interface.")
		},
		"Debug":{
			"logging":(tp.Boolean(),											"Enable Logging",				True),
			"dev_mode":(tp.Boolean(),											"Enable developer mode",		False),
		},
		"Network":{
			"host":(tp.String(),												"Host",							"::",					"Host for your server - most likely :: for IPv6 or 0.0.0.0 for IPv4"),
			"port":(tp.Integer(),												"Port",							42010),
		},
		"Technical":{
			"cache_expire_positive":(tp.Integer(),								"Image Cache Expiration", 							300,	"Days until images are refetched"),
			"cache_expire_negative":(tp.Integer(),								"Image Cache Negative Expiration",					30,		"Days until failed image fetches are reattempted"),
			"use_db_cache":(tp.Boolean(),										"Use DB Cache",										True),
			"cache_database_short":(tp.Boolean(),								"Use volatile Database Cache",						True),
			"cache_database_perm":(tp.Boolean(),								"Use permanent Database Cache",						True),
			"db_cache_entries":(tp.Integer(),									"Maximal Cache entries",							10000),
			"db_max_memory":(tp.Integer(max=100,min=20),						"RAM Percentage Theshold",							75,		"Maximal percentage of RAM that should be used by whole system before Maloja discards cache entries. Use a higher number if your Maloja runs on a dedicated instance (e.g. a container)")
		},
		"Fluff":{
			"scrobbles_gold":(tp.Integer(),										"Scrobbles for Gold",			250,				"How many scrobbles a track needs to be considered 'Gold' status"),
			"scrobbles_platinum":(tp.Integer(),									"Scrobbles for Platinum",		500,				"How many scrobbles a track needs to be considered 'Platinum' status"),
			"scrobbles_diamond":(tp.Integer(),									"Scrobbles for Diamond",		1000,				"How many scrobbles a track needs to be considered 'Diamond' status"),
			"name":(tp.String(),												"Name",							"Generic Maloja User")
		},
		"Third Party Services":{
			"metadata_providers":(tp.List(tp.String()),							"Metadata Providers",			['lastfm','spotify','deezer','musicbrainz'],	"Which metadata providers should be used in what order. Musicbrainz is rate-limited and should not be used first."),
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
			"invalid_artists":(tp.Set(tp.String()),								"Invalid Artists",				["[Unknown Artist]","Unknown Artist","Spotify"],											"Artists that should be discarded immediately"),
			"remove_from_title":(tp.Set(tp.String()),							"Remove from Title",			["(Original Mix)","(Radio Edit)","(Album Version)","(Explicit Version)","(Bonus Track)"],	"Phrases that should be removed from song titles"),
			"delimiters_feat":(tp.Set(tp.String()),								"Featuring Delimiters",			["ft.","ft","feat.","feat","featuring","Ft.","Ft","Feat.","Feat","Featuring"],				"Delimiters used for extra artists, even when in the title field"),
			"delimiters_informal":(tp.Set(tp.String()),							"Informal Delimiters",			["vs.","vs","&"],																			"Delimiters in informal artist strings with spaces expected around them"),
			"delimiters_formal":(tp.Set(tp.String()),							"Formal Delimiters",			[";","/"],																					"Delimiters used to tag multiple artists when only one tag field is available")
		},
		"Web Interface":{
			"default_range_charts_artists":(tp.Choice({'alltime':'All Time','year':'Year','month':"Month",'week':'Week'}),	"Default Range Artist Charts",	"year"),
			"default_range_charts_tracks":(tp.Choice({'alltime':'All Time','year':'Year','month':"Month",'week':'Week'}),	"Default Range Track Charts",	"year"),
			"default_step_pulse":(tp.Choice({'year':'Year','month':"Month",'week':'Week','day':'Day'}),						"Default Pulse Step",			"month"),
			"charts_display_tiles":(tp.Boolean(),								"Display Chart Tiles",			False),
			"discourage_cpu_heavy_stats":(tp.Boolean(),							"Discourage CPU-heavy stats",	False,					"Prevent visitors from mindlessly clicking on CPU-heavy options. Does not actually disable them for malicious actors!"),
			"use_local_images":(tp.Boolean(),									"Use Local Images",				True),
			"local_image_rotate":(tp.Integer(),									"Local Image Rotate",			3600),
			"timezone":(tp.Integer(),											"UTC Offset",					0),
			"time_format":(tp.String(),											"Time Format",					"%d. %b %Y %I:%M %p")
		}
	},
	configfile=newsettingsfile,
	save_endpoint="/apis/mlj_1/settings",
	env_prefix="MALOJA_"

)

malojaconfig["DIRECTORY_CONFIG"] = maloja_dir_config


### STEP 3 - check all possible folders for files (old installation)

directory_info = {
	"cache":{
		"sentinel":"dummy",
		"possible_folders":[
			"/var/cache/maloja",
			"$HOME/.local/share/maloja/cache"
		],
		"setting":"directory_cache"
	},
	"state":{
		"sentinel":"scrobbles",
		"possible_folders":[
			"/var/lib/maloja",
			"$HOME/.local/share/maloja"
		],
		"setting":"directory_state"
	},
	"logs":{
		"sentinel":"dbfix",
		"possible_folders":[
			"/var/log/maloja",
			"$HOME/.local/share/maloja/logs"
		],
		"setting":"directory_logs"
	}
}


for datatype in directory_info:
	info = directory_info[datatype]

	# check if we already have a user-specified setting
	# default obv shouldn't count here, so use get_specified
	if malojaconfig.get_specified(info['setting']) is None and malojaconfig.get_specified('DATA_DIRECTORY') is None:
		# check each possible folder if its used
		for p in info['possible_folders']:
			if os.path.exists(pthj(p,info['sentinel'])):
				print(p,"has been determined as maloja's folder for",datatype)
				malojaconfig[info['setting']] = p
				break
		else:
			print("Could not find previous",datatype,"folder")
			# check which one we can use
			for p in info['possible_folders']:
				if is_dir_usable(p):
					print(p,"has been selected as maloja's folder for",datatype)
					malojaconfig[info['setting']] = p
					break
			else:
				print("No folder can be used for",datatype)
				print("This should not happen!")

if malojaconfig['DATA_DIRECTORY'] is None:
	top_dirs = {
		"config":malojaconfig['DIRECTORY_CONFIG'],
		"state":malojaconfig['DIRECTORY_STATE'],
		"cache":malojaconfig['DIRECTORY_CACHE'],
		"logs":malojaconfig['DIRECTORY_LOGS'],
	}
else:
	top_dirs = {
		"config":malojaconfig['DATA_DIRECTORY'],
		"state":malojaconfig['DATA_DIRECTORY'],
		"cache":pthj(malojaconfig['DATA_DIRECTORY'],"cache"),
		"logs":pthj(malojaconfig['DATA_DIRECTORY'],"logs"),
	}



data_directories = {
	"auth":pthj(top_dirs['state'],"auth"),
	"backups":pthj(top_dirs['state'],"backups"),
	"images":pthj(top_dirs['state'],"images"),
	"scrobbles":pthj(top_dirs['state'],"scrobbles"),
	"rules":pthj(top_dirs['config'],"rules"),
	"clients":pthj(top_dirs['config'],"clients"),
	"settings":pthj(top_dirs['config']),
	"css":pthj(top_dirs['config'],"custom_css"),
	"logs":pthj(top_dirs['logs']),
	"cache":pthj(top_dirs['cache']),
}


data_dir = {
	k:lambda *x,k=k: pthj(data_directories[k],*x)  for k in data_directories
}





### DOREAH CONFIGURATION

from doreah import config

config(
	caching={
		"folder": data_dir['cache']()
	},
	auth={
		"multiuser":False,
		"cookieprefix":"maloja",
		"stylesheets":["/style.css"],
		"dbfile":data_dir['auth']("auth.ddb")
	},
	logging={
		"logfolder": data_dir['logs']() if malojaconfig["LOGGING"] else None
	},
	regular={
		"autostart": False,
		"offset": malojaconfig["TIMEZONE"]
	}
)

settingsconfig._readpreconfig()
