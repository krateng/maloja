### PACKAGE DATA

name = "maloja"
desc = "Self-hosted music scrobble database"
author = {
	"name":"Johannes Krattenmacher",
	"email":"maloja@krateng.dev",
	"github": "krateng"
}
version = 2,2,4
versionstr = ".".join(str(n) for n in version)


requires = [
	"bottle>=0.12.16",
	"waitress>=1.3",
	"doreah>=1.4.5",
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
	"data_files/*/*/*"
]

commands = {
	"maloja":"controller:main"
}

from . import globalconf
