name = "maloja"

from .info import author,version,versionstr

requires = [
	"bottle>=0.12.16",
	"waitress>=1.3",
	"doreah>=1.2.9",
	"nimrodel>=0.4.9",
	"setproctitle>=1.1.10",
	"wand>=0.5.4",
	"lesscpy>=0.13"
]
resources = [
	"website/*/*",
	"website/*",
	"data_files/*/*",
	"data_files/.doreah"
]
