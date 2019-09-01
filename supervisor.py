#!/usr/bin/env python3

import subprocess
import time
import setproctitle
import signal


setproctitle.setproctitle("maloja_supervisor")


while True:
	time.sleep(60)

	try:
		output = subprocess.check_output(["pidof","Maloja"])
		pid = int(output)
	except:
		print("Maloja not running, restarting...")
		p = subprocess.Popen(["python3","server.py"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
