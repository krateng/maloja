name = "maloja"

from .info import author,version,versionstr

requires = [
	"bottle>=0.12.16",
	"waitress>=1.3",
	"doreah>=1.2.10",
	"nimrodel>=0.4.9",
	"setproctitle>=1.1.10",
	"wand>=0.5.4",
	"lesscpy>=0.13"
]
resources = [
	"web/*/*",
	"web/*",
	"data_files/*/*",
	"data_files/.doreah"
]

commands = {
	"maloja":"controller:main"
}

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
