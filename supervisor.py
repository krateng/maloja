#!/usr/bin/env python3

import subprocess
import time
import setproctitle
import signal
from doreah.logging import log


setproctitle.setproctitle("maloja_supervisor")


while True:
	time.sleep(60)

	try:
		output = subprocess.check_output(["pidof","Maloja"])
		pid = int(output)
		log("Maloja is running, PID " + str(pid),module="supervisor")
	except:
		log("Maloja is not running, restarting...",module="supervisor")
		try:
			p = subprocess.Popen(["python3","server.py"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
		except e:
			log("Error starting Maloja: " + str(e),module="supervisor")
