import os
import signal
import subprocess
import time

from setproctitle import setproctitle
from ipaddress import ip_address

from doreah.control import mainfunction
from doreah.io import col
from doreah.logging import log

from . import __pkginfo__ as pkginfo
from .pkg_global import conf
from .proccontrol import tasks
from .setup import setup
from .dev import generate, apidebug



def print_header_info():
	print()
	#print("#####")
	print(col['yellow']("Maloja"),f"v{pkginfo.VERSION}")
	print(pkginfo.HOMEPAGE)
	#print("#####")
	print()

def onlysetup():
	print_header_info()
	setup()
	print("Setup complete!")

def run_server():
	print_header_info()
	setup()
	setproctitle("maloja")
	from . import server
	server.run_server()

def debug():
	os.environ["MALOJA_DEV_MODE"] = 'true'
	conf.malojaconfig.load_environment()
	run_server()

def print_info():
	print_header_info()
	print(col['lightblue']("Configuration Directory:"),conf.dir_settings['config'])
	print(col['lightblue']("State Directory:        "),conf.dir_settings['state'])
	print(col['lightblue']("Log Directory:          "),conf.dir_settings['logs'])
	print(col['lightblue']("Network:                "),f"Dual Stack, Port {conf.malojaconfig['port']}" if conf.malojaconfig['host'] == "*" else f"IPv{ip_address(conf.malojaconfig['host']).version}, Port {conf.malojaconfig['port']}")
	print(col['lightblue']("Timezone:               "),f"UTC{conf.malojaconfig['timezone']:+d}")
	print(col['lightblue']("Location Timezone:      "),conf.malojaconfig['location_timezone'])
	print()
	try:
		from importlib.metadata import distribution
		for pkg in ("sqlalchemy","waitress","bottle","doreah","jinja2"):
			print(col['cyan'](f"{pkg}:".ljust(13)),distribution(pkg).version)
	except Exception:
		print("Could not determine dependency versions.")
	print()
	try:
		import platform
		pyimpl = platform.python_implementation()
		pyvers = '.'.join(platform.python_version_tuple())
		print(col['magenta'](f"Python:".ljust(13)),pyimpl,pyvers)
		osname = platform.system()
		osvers = platform.release()
		print(col['magenta'](f"OS:".ljust(13)),osname,osvers)
		arch = platform.machine()
		print(col['magenta'](f"Architecture:".ljust(13)),arch)
	except Exception:
		print("Could not determine system information.")


def print_settings():
	print_header_info()
	maxlen = max(len(k) for k in conf.malojaconfig)
	for k in conf.malojaconfig:
		print(col['lightblue'](k.ljust(maxlen+2)),conf.malojaconfig[k])


@mainfunction({"l":"level","v":"version","V":"version"},flags=['version','include_images','prefer_existing'],shield=True)
def main(*args,**kwargs):

	actions = {
		# server
		"run":run_server,
		"debug":debug,
		"setup":onlysetup,
		# admin scripts
		"import":tasks.import_scrobbles,		# maloja import /x/y.csv
		"backup":tasks.backup,					# maloja backup --targetfolder /x/y --include_images
		"generate":generate.generate_scrobbles,	# maloja generate 400
		"export":tasks.export,					# maloja export
		"apidebug":apidebug.run,				# maloja apidebug
		"parsealbums":tasks.parse_albums,		# maloja parsealbums --strategy majority
		# aux
		"info":print_info,
		"settings":print_settings
	}

	if "version" in kwargs:
		print(pkginfo.VERSION)
		return True
	else:
		try:
			action, *args = args
			action = actions[action]
		except (ValueError, KeyError):
			print("Valid commands: " + " ".join(a for a in actions))
			return False

		return action(*args,**kwargs)
