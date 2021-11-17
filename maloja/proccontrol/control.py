import subprocess
from doreah import settings
from doreah.control import mainfunction
from doreah.io import col
import os
import signal

from .setup import setup
from . import tasks
from .. import __pkginfo__ as info

print()
print("#####")
print("Maloja v" + info.versionstr)
print("https://github.com/" + info.author['github'] + "/" + info.links['github'])
print("#####")
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
		setup()
		try:
			#p = subprocess.Popen(["python3","-m","maloja.server"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
			sp = subprocess.Popen(["python3","-m","maloja.proccontrol.supervisor"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
			print(col["green"]("Maloja started!"))

			port = settings.get_settings("WEB_PORT")

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



def direct():
	setup()
	from .. import server


@mainfunction({"l":"level"},shield=True)
def main(action,*args,**kwargs):
	actions = {
		"start":start,
		"restart":restart,
		"stop":stop,
		"run":direct,
		"debug":direct,

		"import":tasks.loadlastfm,
		"backup":tasks.backuphere,
	#	"update":update,
		"fix":tasks.fixdb,
		"generate":tasks.generate_scrobbles
	}
	if action in actions: actions[action](*args,**kwargs)
	else: print("Valid commands: " + " ".join(a for a in actions))

	return True
