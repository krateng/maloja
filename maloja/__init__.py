### PACKAGE DATA

name = "maloja"
desc = "Self-hosted music scrobble database"
author = {
	"name":"Johannes Krattenmacher",
	"email":"maloja@krateng.dev",
	"github": "krateng"
}
version = 2,1,4
versionstr = ".".join(str(n) for n in version)


requires = [
	"bottle>=0.12.16",
	"waitress>=1.3",
	"doreah>=1.2.10",
	"nimrodel>=0.6.3",
	"setproctitle>=1.1.10",
	"wand>=0.5.4",
	"lesscpy>=0.13"
]
resources = [
	"web/*/*",
	"web/*",
	"static/*/*",
	"data_files/*/*",
	"data_files/*/*/*",
	"data_files/.doreah"
]

commands = {
	"maloja":"controller:main"
}

### DOREAH CONFIGURATION

from doreah import config
config(
	logging={
		"logfolder": "logs"
	},
	settings={
		"files":[
			"settings/default.ini",
			"settings/settings.ini"
		]
	},
	caching={
		"folder": "cache/"
	},
	regular={
		"autostart": False
	}
)


### USER DATA FOLDER


import os
try:
	DATA_DIR = os.environ["XDG_DATA_HOME"].split(":")[0]
	assert os.path.exists(DATA_DIR)
except:
	DATA_DIR = os.path.join(os.environ["HOME"],".local/share/")

DATA_DIR = os.path.join(DATA_DIR,"maloja")
os.makedirs(DATA_DIR,exist_ok=True)
