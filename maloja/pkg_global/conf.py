import os

import doreah.auth
import doreah.logging
from doreah.configuration import Configuration
from doreah.configuration import types as tp


from ..__pkginfo__ import VERSION


# this mode specifies whether we run some auxiliary task instead of the main server
AUX_MODE = True


# if DATA_DIRECTORY is specified, this is the directory to use for EVERYTHING, no matter what
# but with asynnetrical structure, cache and logs in subfolders
# otherwise, each directory is treated seperately
# in that case, individual settings for each are respected
# DIRECRORY_CONFIG, DIRECRORY_STATE, DIRECTORY_LOGS and DIRECTORY_CACHE
# config can only be determined by environment variable, the others can be loaded
# from the config files

# we don't specify 'default' values in the normal sense of the config object
# the default is none, meaning the app should figure it out (depending on environment)
# the actual 'default' values of our folders are simply in code since they are dependent on environment (container?)
# and we need to actually distinguish them from the user having specified something

# USEFUL FUNCS
pthj = os.path.join

def is_dir_usable(pth):
	try:
		os.makedirs(pth,exist_ok=True)
		return os.access(pth,os.W_OK)
	except Exception:
		return False

def get_env_vars(key,pathsuffix=[]):
	return [pthj(pth,*pathsuffix) for pth in os.environ.get(key,'').split(':') if pth != '']



directory_info = {
	"config":{
		"sentinel":".maloja_config_sentinel",
		"possible_folders_container":[
			"/config/config"
		],
		"possible_folders":[
			"/etc/maloja",
			os.path.expanduser("~/.local/share/maloja")
		],
		"setting":"directory_config"
	},
	"cache":{
		"sentinel":".maloja_cache_sentinel",
		"possible_folders_container":[
			"/config/cache"
		],
		"possible_folders":[
			"/var/cache/maloja",
			os.path.expanduser("~/.local/share/maloja/cache"),
			"/tmp/maloja"
		],
		"setting":"directory_cache"
	},
	"state":{
		"sentinel":".maloja_state_sentinel",
		"possible_folders_container":[
			"/config/state"
		],
		"possible_folders":[
			"/var/lib/maloja",
			os.path.expanduser("~/.local/share/maloja")
		],
		"setting":"directory_state"
	},
	"logs":{
		"sentinel":".maloja_logs_sentinel",
		"possible_folders_container":[
			"/config/logs"
		],
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
def find_good_folder(datatype):
	info = directory_info[datatype]

	possible_folders = info['possible_folders']
	if os.environ.get("MALOJA_CONTAINER"):
		possible_folders = info['possible_folders_container'] + possible_folders

	# check each possible folder if its used
	for p in possible_folders:
		if os.path.exists(pthj(p,info['sentinel'])):
			if is_dir_usable(p):
				#print(p,"was apparently used as maloja's folder for",datatype,"- fixing in settings")
				return p
			else:
				raise PermissionError(f"Can no longer use previously used {datatype} folder {p}")

	#print("Could not find previous",datatype,"folder")
	# check which one we can use
	for p in possible_folders:
		if is_dir_usable(p):
			#print(p,"has been selected as maloja's folder for",datatype)
			return p
	#print("No folder can be used for",datatype)
	#print("This should not happen!")
	raise PermissionError(f"No folder could be found for {datatype}")





### STEP 1 - find out where the settings file is

maloja_dir_config = os.environ.get("MALOJA_DATA_DIRECTORY") or os.environ.get("MALOJA_DIRECTORY_CONFIG")

if maloja_dir_config is None:
	# if nothing is set, we set our own
	maloja_dir_config = find_good_folder('config')
else:
	pass
	# if there is an environment variable, this is 100% explicitly defined by the user, so we respect it
	# the user might run more than one instances on the same machine, so we don't do any heuristics here
	# if you define this, we believe it!

os.makedirs(maloja_dir_config,exist_ok=True)
settingsfile = pthj(maloja_dir_config,"settings.ini")


### STEP 2 - create settings object


malojaconfig = Configuration(
	settings={
		"Setup":{
			"data_directory":(tp.String(),										"Data Directory",				None,					"Folder for all user data. Overwrites all choices for specific directories."),
			"directory_config":(tp.String(),									"Config Directory",				None,					"Folder for config data. Only applied when global data directory is not set."),
			"directory_state":(tp.String(),										"State Directory",				None,					"Folder for state data. Only applied when global data directory is not set."),
			"directory_logs":(tp.String(),										"Log Directory",				None,					"Folder for log data. Only applied when global data directory is not set."),
			"directory_cache":(tp.String(),										"Cache Directory",				None,					"Folder for cache data. Only applied when global data directory is not set."),
			"skip_setup":(tp.Boolean(),											"Skip Setup",					False,					"Make server setup process non-interactive. Vital for Docker."),
			"force_password":(tp.String(),										"Force Password",				None,					"On startup, overwrite admin password with this one. This should usually only be done via environment variable in Docker."),
			"clean_output":(tp.Boolean(),										"Avoid Mutable Console Output",	False,					"Use if console output will be redirected e.g. to a web interface.")
		},
		"Debug":{
			"logging":(tp.Boolean(),											"Enable Logging",				True),
			"dev_mode":(tp.Boolean(),											"Enable developer mode",		False),
		},
		"Network":{
			"host":(tp.String(),												"Host",							"*",					"Host for your server, e.g. '*' for dual stack, '::' for IPv6 or '0.0.0.0' for IPv4"),
			"port":(tp.Integer(),												"Port",							42010),
		},
		"Technical":{
			"cache_expire_positive":(tp.Integer(),								"Image Cache Expiration", 				60,		"Days until images are refetched"),
			"cache_expire_negative":(tp.Integer(),								"Image Cache Negative Expiration",		5,		"Days until failed image fetches are reattempted"),
			"db_max_memory":(tp.Integer(min=0,max=100),							"RAM Percentage soft limit",			70,		"RAM Usage in percent at which Maloja should no longer increase its database cache."),
			"use_request_cache":(tp.Boolean(),									"Use request-local DB Cache",			False),
			"use_global_cache":(tp.Boolean(),									"Use global DB Cache",					True,	"This is vital for Maloja's performance. Do not disable this unless you have a strong reason to.")
		},
		"Fluff":{
			"scrobbles_gold":(tp.Integer(),										"Scrobbles for Gold (Track)",	250,				"How many scrobbles a track needs to be considered 'Gold' status"),
			"scrobbles_platinum":(tp.Integer(),									"Scrobbles for Platinum (Track)",500,				"How many scrobbles a track needs to be considered 'Platinum' status"),
			"scrobbles_diamond":(tp.Integer(),									"Scrobbles for Diamond (Track)",1000,				"How many scrobbles a track needs to be considered 'Diamond' status"),
			"scrobbles_gold_album":(tp.Integer(),								"Scrobbles for Gold (Album)",	500,				"How many scrobbles an album needs to be considered 'Gold' status"),
			"scrobbles_platinum_album":(tp.Integer(),							"Scrobbles for Platinum (Album)",750,				"How many scrobbles an album needs to be considered 'Platinum' status"),
			"scrobbles_diamond_album":(tp.Integer(),							"Scrobbles for Diamond (Album)",1500,				"How many scrobbles an album needs to be considered 'Diamond' status"),
			"name":(tp.String(),												"Name",							"Generic Maloja User")
		},
		"Third Party Services":{
			"metadata_providers":(tp.List(tp.String()),							"Metadata Providers",			['lastfm','spotify','deezer','audiodb','musicbrainz'],	"List of which metadata providers should be used in what order. Musicbrainz is rate-limited and should not be used first."),
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
			"proxy_images":(tp.Boolean(),										"Image Proxy",					True,	"Whether third party images should be downloaded and served directly by Maloja (instead of just linking their URL)")

		},
		"Database":{
			"album_information_trust":(tp.Choice({'first':"First",'last':"Last",'majority':"Majority"}),	"Album Information Authority","first",															"Whether to trust the first album information that is sent with a track or update every time a different album is sent"),
			"invalid_artists":(tp.Set(tp.String()),								"Invalid Artists",				["[Unknown Artist]","Unknown Artist","Spotify"],											"Artists that should be discarded immediately"),
			"remove_from_title":(tp.Set(tp.String()),							"Remove from Title",			["(Original Mix)","(Radio Edit)","(Album Version)","(Explicit Version)","(Bonus Track)"],	"Phrases that should be removed from song titles"),
			"delimiters_feat":(tp.Set(tp.String()),								"Featuring Delimiters",			["ft.","ft","feat.","feat","featuring"],													"Delimiters used for extra artists, even when in the title field"),
			"delimiters_informal":(tp.Set(tp.String()),							"Informal Delimiters",			["vs.","vs","&"],																			"Delimiters in informal artist strings with spaces expected around them"),
			"delimiters_formal":(tp.Set(tp.String()),							"Formal Delimiters",			[";","/","|","␝","␞","␟"],																	"Delimiters used to tag multiple artists when only one tag field is available"),
			"filters_remix":(tp.Set(tp.String()),								"Remix Filters",				["Remix", "Remix Edit", "Short Mix", "Extended Mix", "Soundtrack Version"],					"Filters used to recognize the remix artists in the title"),
			"parse_remix_artists":(tp.Boolean(),								"Parse Remix Artists",			False),
			"week_offset":(tp.Integer(),										"Week Begin Offset",			0,																							"Start of the week for the purpose of weekly statistics. 0 = Sunday, 6 = Saturday"),
			"timezone":(tp.Integer(),											"UTC Offset",					0)
		},
		"Web Interface":{
			"default_range_startpage":(tp.Choice({'alltime':'All Time','year':'Year','month':"Month",'week':'Week'}),	"Default Range for Startpage Stats",	"year"),
			"default_step_pulse":(tp.Choice({'year':'Year','month':"Month",'week':'Week','day':'Day'}),						"Default Pulse Step",			"month"),
			"charts_display_tiles":(tp.Boolean(),								"Display Chart Tiles",			False),
			"album_showcase":(tp.Boolean(),										"Display Album Showcase",		True,		"Display a graphical album showcase for artist overview pages instead of a chart list"),
			"display_art_icons":(tp.Boolean(),									"Display Album/Artist Icons",	True),
			"default_album_artist":(tp.String(),								"Default Albumartist",			"Various Artists"),
			"use_album_artwork_for_tracks":(tp.Boolean(),						"Use Album Artwork for tracks",	True),
			"fancy_placeholder_art":(tp.Boolean(),								"Use fancy placeholder artwork",False),
			"show_play_number_on_tiles":(tp.Boolean(),							"Show amount of plays on tiles",False),
			"discourage_cpu_heavy_stats":(tp.Boolean(),							"Discourage CPU-heavy stats",	False,					"Prevent visitors from mindlessly clicking on CPU-heavy options. Does not actually disable them for malicious actors!"),
			"use_local_images":(tp.Boolean(),									"Use Local Images",				True),
			#"local_image_rotate":(tp.Integer(),									"Local Image Rotate",			3600),
			"time_format":(tp.String(),											"Time Format",					"%d. %b %Y %I:%M %p"),
			"theme":(tp.String(),												"Theme",						"maloja")
		}
	},
	configfile=settingsfile,
	save_endpoint="/apis/mlj_1/settings",
	env_prefix="MALOJA_",
	extra_files=["/run/secrets/maloja.yml","/run/secrets/maloja.ini"]

)

if not malojaconfig.readonly:
	malojaconfig["DIRECTORY_CONFIG"] = maloja_dir_config
	# this really doesn't matter because when are we gonna load info about where
	# the settings file is stored from the settings file
	# but oh well

try:
	malojaconfig.render_help(pthj(maloja_dir_config,"settings.md"),
		top_text='''If you wish to adjust settings in the settings.ini file, do so while the server
	is not running in order to avoid data being overwritten.

	Technically, each setting can be set via environment variable or the settings
	file - simply add the prefix `MALOJA_` for environment variables. It is recommended
	to use the settings file where possible and not configure each aspect of your
	server via environment variables!

	You also can specify additional settings in the files`/run/secrets/maloja.yml` or
	`/run/secrets/maloja.ini`, as well as their values directly in files of the respective
	name in `/run/secrets/` (e.g. `/run/secrets/lastfm_api_key`).''')
except PermissionError as e:
	pass


### STEP 3 - now check the other directories


if not malojaconfig.readonly:
	for datatype in ("state","cache","logs"):
		# if the setting is specified in the file or via a user environment variable, we accept it (we'll check later if it's usable)
		if malojaconfig[directory_info[datatype]['setting']] or malojaconfig['DATA_DIRECTORY']:
			pass
		# otherwise, find a good one
		else:
			malojaconfig[directory_info[datatype]['setting']] = find_good_folder(datatype)







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
	"scrobbles":pthj(dir_settings['state']),
	"rules":pthj(dir_settings['config'],"rules"),
	"clients":pthj(dir_settings['config']),
	"settings":pthj(dir_settings['config']),
	"css":pthj(dir_settings['config'],"custom_css"),

	"config":dir_settings['config'],
	"state":dir_settings['state'],
	"logs":dir_settings['logs'],
	"cache":dir_settings['cache'],
}

for identifier,path in data_directories.items():
	try:
		os.makedirs(path,exist_ok=True)
		if not is_dir_usable(path): raise PermissionError(f"Directory {path} is not usable!")
	except PermissionError:
		# special case: cache does not contain info that can't be refetched, so no need to require user intervention
		# just move to the next one
		if identifier in ['cache']:
			print("Cannot use",path,"for cache, finding new folder...")
			data_directories['cache'] = dir_settings['cache'] = malojaconfig['DIRECTORY_CACHE'] = find_good_folder('cache')
		else:
			print("Directory",path,"is not usable.")
			print("Please change permissions or settings!")
			print("Make sure Maloja has write and execute access to this directory.")
			raise


data_dir = {
	k:lambda *x,k=k: pthj(data_directories[k],*x)  for k in data_directories
}



### DOREAH OBJECTS

auth = doreah.auth.AuthManager(singleuser=True,cookieprefix='maloja',stylesheets=("/maloja.css",),dbfile=data_dir['auth']("auth.sqlite"))

#logger = doreah.logging.Logger(logfolder=data_dir['logs']() if malojaconfig["LOGGING"] else None)
#log = logger.log

# this is not how its supposed to be done, but lets ease the transition
doreah.logging.defaultlogger.logfolder = data_dir['logs']() if malojaconfig["LOGGING"] else None



custom_css_files = [f for f in os.listdir(data_dir['css']()) if f.lower().endswith('.css')]

from ..database.sqldb import set_maloja_info
set_maloja_info({'last_run_version':VERSION})

# what the fuck did i just write
# this spaghetti file is proudly sponsored by the rice crackers i'm eating at the
# moment as well as some cute chinese girl whose asmr i'm listening to in the
# background. and now to bed!
