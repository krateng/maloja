#!/usr/bin/env python3
import os

import subprocess
import time
import setproctitle
import signal
from doreah.logging import log
from doreah.settings import get_settings


setproctitle.setproctitle("maloja_supervisor")


while True:
	time.sleep(60)

	try:
		output = subprocess.check_output(["pidof","Maloja"])
		pid = int(output)
	except:
		log("Maloja is not running, restarting...",module="supervisor")
		if get_settings("UPDATE_AFTER_CRASH"):
			log("Updating first...",module="supervisor")
			try:
				os.system("pip3 install maloja --upgrade --no-cache-dir")
			except:
				log("Could not update.",module="supervisor")
		try:
			p = subprocess.Popen(["python3","-m","maloja.server"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
		except e:
			log("Error starting Maloja: " + str(e),module="supervisor")
