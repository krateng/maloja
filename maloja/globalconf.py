import os
from doreah.configuration import Configuration
from doreah.configuration import types as tp
from doreah.keystore import KeyStore

from .__pkginfo__ import VERSION



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



directory_info = {
	"config":{
		"sentinel":"rules",
		"possible_folders":[
			"/etc/maloja",
			os.path.expanduser("~/.local/share/maloja")
		],
		"setting":"directory_config"
	},
	"cache":{
		"sentinel":"dummy",
		"possible_folders":[
			"/var/cache/maloja",
			os.path.expanduser("~/.local/share/maloja/cache")
		],
		"setting":"directory_cache"
	},
	"state":{
		"sentinel":"scrobbles",
		"possible_folders":[
			"/var/lib/maloja",
			os.path.expanduser("~/.local/share/maloja")
		],
		"setting":"directory_state"
	},
	"logs":{
		"sentinel":"dbfix",
		"possible_folders":[
			"/var/log/maloja",
			os.path.expanduser("~/.local/share/maloja/logs")
		],
		"setting":"directory_logs"
	}
}

# function that
#   checks if one has been in use before and writes it to dict/config
#   if not, determines which to use and writes it to dict/config
# returns determined folder
def find_good_folder(datatype,configobject):
	info = directory_info[datatype]

	# check each possible folder if its used
	for p in info['possible_folders']:
		if os.path.exists(pthj(p,info['sentinel'])):
			#print(p,"has been determined as maloja's folder for",datatype)
			configobject[info['setting']] = p
			return p

	#print("Could not find previous",datatype,"folder")
	# check which one we can use
	for p in info['possible_folders']:
		if is_dir_usable(p):
			#print(p,"has been selected as maloja's folder for",datatype)
			configobject[info['setting']] = p
			return p
	#print("No folder can be used for",datatype)
	#print("This should not happen!")





### STEP 1 - find out where the settings file is
# environment variables
maloja_dir_config = os.environ.get("MALOJA_DATA_DIRECTORY") or os.environ.get("MALOJA_DIRECTORY_CONFIG")


if maloja_dir_config is None:
	maloja_dir_config = find_good_folder('config',{})
	found_new_config_dir = True
else:
	found_new_config_dir = False
	# remember whether we had to find our config dir or it was user-specified

os.makedirs(maloja_dir_config,exist_ok=True)

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
			"lastfm_api_sk":(tp.String(),										"Last.fm API Session Key",		None),
			"lastfm_username":(tp.String(),										"Last.fm Username",				None),
			"lastfm_password":(tp.String(),										"Last.fm Password",				None),
			"spotify_api_id":(tp.String(),										"Spotify API ID",				None),
			"spotify_api_secret":(tp.String(),									"Spotify API Secret",			None),
			"audiodb_api_key":(tp.String(),										"TheAudioDB API Key",			None),
			"other_maloja_url":(tp.String(),									"Other Maloja Instance URL",	None),
			"other_maloja_api_key":(tp.String(),								"Other Maloja Instance API Key",None),
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

if found_new_config_dir:
	malojaconfig["DIRECTORY_CONFIG"] = maloja_dir_config
	# this really doesn't matter because when are we gonna load info about where
	# the settings file is stored from the settings file
	# but oh well

malojaconfig.render_help(pthj(maloja_dir_config,"settings.md"),
	top_text='''If you wish to adjust settings in the settings.ini file, do so while the server
is not running in order to avoid data being overwritten.

Technically, each setting can be set via environment variable or the settings
file - simply add the prefix `MALOJA_` for environment variables. It is recommended
to use the settings file where possible and not configure each aspect of your
server via environment variables!''')


### STEP 3 - check all possible folders for files (old installation)




for datatype in ("state","cache","logs"):
	# obviously default values shouldn't trigger this
	# if user has nothing specified, we need to use this
	if malojaconfig.get_specified(directory_info[datatype]['setting']) is None and malojaconfig.get_specified('DATA_DIRECTORY') is None:
		find_good_folder(datatype,malojaconfig)








### STEP 4 - this is where all the guessing about previous installation ends
###          we have our definite settings and are now just generating the real
###          folder names for everything


if malojaconfig['DATA_DIRECTORY'] is None:
	dir_settings = {
		"config":malojaconfig['DIRECTORY_CONFIG'],
		"state":malojaconfig['DIRECTORY_STATE'],
		"cache":malojaconfig['DIRECTORY_CACHE'],
		"logs":malojaconfig['DIRECTORY_LOGS'],
	}
else:
	dir_settings = {
		"config":malojaconfig['DATA_DIRECTORY'],
		"state":malojaconfig['DATA_DIRECTORY'],
		"cache":pthj(malojaconfig['DATA_DIRECTORY'],"cache"),
		"logs":pthj(malojaconfig['DATA_DIRECTORY'],"logs"),
	}


data_directories = {
	"auth":pthj(dir_settings['state'],"auth"),
	"backups":pthj(dir_settings['state'],"backups"),
	"images":pthj(dir_settings['state'],"images"),
	"scrobbles":pthj(dir_settings['state'],"scrobbles"),
	"rules":pthj(dir_settings['config'],"rules"),
	"clients":pthj(dir_settings['config']),
	"settings":pthj(dir_settings['config']),
	"css":pthj(dir_settings['config'],"custom_css"),
	"logs":pthj(dir_settings['logs']),
	"cache":pthj(dir_settings['cache']),
}


data_dir = {
	k:lambda *x,k=k: pthj(data_directories[k],*x)  for k in data_directories
}



### write down the last ran version
with open(pthj(dir_settings['state'],".lastmalojaversion"),"w") as filed:
	filed.write(VERSION)
	filed.write("\n")





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




### API KEYS



### symmetric keys are fine for now since we hopefully use HTTPS
apikeystore = KeyStore(file=data_dir['clients']("apikeys.yml"),save_endpoint="/apis/mlj_1/apikeys")

oldfile = pthj(dir_settings['config'],"clients","authenticated_machines.tsv")
if os.path.exists(oldfile):
	try:
		from doreah import tsv
		clients = tsv.parse(oldfile,"string","string")
		for key,identifier in clients:
			apikeystore[identifier] = key
		os.remove(oldfile)
	except:
		pass


# what the fuck did i just write
# this spaghetti file is proudly sponsored by the rice crackers i'm eating at the
# moment as well as some cute chinese girl whose asmr i'm listening to in the
# background. and now to bed!
