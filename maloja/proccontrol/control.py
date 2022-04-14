import subprocess
from doreah import settings
from doreah.control import mainfunction
from doreah.io import col
import os
import signal
from ipaddress import ip_address

from .setup import setup
from . import tasks
from .. import __pkginfo__ as info
from .. import globalconf



def print_header_info():
	print()
	#print("#####")
	print(col['yellow']("Maloja"),"v" + info.VERSION)
	print(info.HOMEPAGE)
	#print("#####")
	print()



def getInstance():
	try:
		output = subprocess.check_output(["pidof","Maloja"])
		return int(output)
	except:
		return None

def getInstanceSupervisor():
	try:
		output = subprocess.check_output(["pidof","maloja_supervisor"])
		return int(output)
	except:
		return None

def restart():
	stop()
	start()

def start():
	if getInstanceSupervisor() is not None:
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

	pid_sv = getInstanceSupervisor()
	if pid_sv is not None:
		os.kill(pid_sv,signal.SIGTERM)

	pid = getInstance()
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

def direct():
	print_header_info()
	setup()
	from .. import server
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
		"run":direct,
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
		return True
	else:
		try:
			action, *args = args
			action = actions[action]
		except (ValueError, KeyError):
			print("Valid commands: " + " ".join(a for a in actions))
			return False

		return action(*args,**kwargs)
