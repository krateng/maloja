name = "maloja"
desc = "Self-hosted music scrobble database"
author = {
	"name":"Johannes Krattenmacher",
	"email":"maloja@krateng.dev",
	"github": "krateng"
}
version = 2,6,6
versionstr = ".".join(str(n) for n in version)
links = {
	"pypi":"malojaserver",
	"github":"maloja"
}

requires = [
	"bottle>=0.12.16",
	"waitress>=1.3",
	"doreah>=1.6.7",
	"nimrodel>=0.6.3",
	"setproctitle>=1.1.10",
	"wand>=0.5.4",
	"lesscpy>=0.13",
	"jinja2>2.11",
	"lru-dict>=1.1.6"
]
resources = [
	"web/*/*/*",
	"web/*/*",
	"web/*",
	"static/*/*",
	"data_files/*/*",
	"data_files/*/*/*",
	"*/*.py",
	"*/*/*.py",
	"*/*/*/*.py"
]

commands = {
	"maloja":"proccontrol.control:main"
}
