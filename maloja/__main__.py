import os
import signal
import subprocess

from setproctitle import setproctitle
from ipaddress import ip_address

from doreah.control import mainfunction
from doreah.io import col

from . import __pkginfo__ as pkginfo
from . import globalconf
from .proccontrol import tasks
from .proccontrol.setup import setup



def print_header_info():
	print()
	#print("#####")
	print(col['yellow']("Maloja"),f"v{pkginfo.VERSION}")
	print(pkginfo.HOMEPAGE)
	#print("#####")
	print()



def get_instance():
	try:
		return int(subprocess.check_output(["pidof","maloja"]))
	except:
		return None

def get_instance_supervisor():
	try:
		return int(subprocess.check_output(["pidof","maloja_supervisor"]))
	except:
		return None

def restart():
	stop()
	start()


def start():
	if get_instance_supervisor() is not None:
		print("Maloja is already running.")
	else:
		print_header_info()
		setup()
		try:
			#p = subprocess.Popen(["python3","-m","maloja.server"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
			sp = subprocess.Popen(["python3","-m","maloja.proccontrol.supervisor"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
			print(col["green"]("Maloja started!"))

			port = globalconf.malojaconfig["PORT"]

			print("Visit your server address (Port " + str(port) + ") to see your web interface. Visit /admin_setup to get started.")
			print("If you're installing this on your local machine, these links should get you there:")
			print("\t" + col["blue"]("http://localhost:" + str(port)))
			print("\t" + col["blue"]("http://localhost:" + str(port) + "/admin_setup"))
			return True
		except:
			print("Error while starting Maloja.")
			return False


def stop():

	pid_sv = get_instance_supervisor()
	if pid_sv is not None:
		os.kill(pid_sv,signal.SIGTERM)

	pid = get_instance()
	if pid is not None:
		os.kill(pid,signal.SIGTERM)

	if pid is None and pid_sv is None:
		return False

	print("Maloja stopped!")
	return True

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
	globalconf.malojaconfig.load_environment()
	direct()

def print_info():
	print_header_info()
	print(col['lightblue']("Configuration Directory:"),globalconf.dir_settings['config'])
	print(col['lightblue']("Data Directory:         "),globalconf.dir_settings['state'])
	print(col['lightblue']("Log Directory:          "),globalconf.dir_settings['logs'])
	print(col['lightblue']("Network:                "),f"IPv{ip_address(globalconf.malojaconfig['host']).version}, Port {globalconf.malojaconfig['port']}")
	print(col['lightblue']("Timezone:               "),f"UTC{globalconf.malojaconfig['timezone']:+d}")
	print()
	print()

@mainfunction({"l":"level","v":"version","V":"version"},flags=['version','include_images'],shield=True)
def main(*args,**kwargs):

	actions = {
		# server
		"start":start,
		"restart":restart,
		"stop":stop,
		"run":run_server,
		"debug":debug,
		"setup":onlysetup,
		# admin scripts
		"import":tasks.import_scrobbles,		# maloja import /x/y.csv
		"backup":tasks.backup,					# maloja backup --targetfolder /x/y --include_images
		"generate":tasks.generate,				# maloja generate 400
		"export":tasks.export,					# maloja export
		# aux
		"info":print_info
	}

	if "version" in kwargs:
		print(info.VERSION)
	else:
		try:
			action, *args = args
			action = actions[action]
		except (ValueError, KeyError):
			print("Valid commands: " + " ".join(a for a in actions))
			return

		return action(*args,**kwargs)

	return True
