#!/usr/bin/env python3
import os

import subprocess
import time
import setproctitle
import signal
from datetime import datetime
from doreah.logging import log
from doreah.settings import get_settings


setproctitle.setproctitle("maloja_supervisor")

lastrestart = ()

def get_pid():
	try:
		output = subprocess.check_output(["pidof","Maloja"])
		return int(output)
	except:
		return None

def update():
	log("Updating...",module="supervisor")
	try:
		os.system("pip3 install maloja --upgrade --no-cache-dir")
	except:
		log("Could not update.",module="supervisor")

def start():
	try:
		p = subprocess.Popen(["python3","-m","maloja.server"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

	except e:
		log("Error starting Maloja: " + str(e),module="supervisor")



while True:


	now = datetime.now()
	today = now.year, now.month, now.day

	pid = get_pid()

	if pid:

		restart = get_settings("DAILY_RESTART")
		if restart not in [None,False]:
			if today != lastrestart:
				if now.hour == restart:
					log("Daily restart...",module="supervisor")
					os.kill(pid,signal.SIGTERM)
					start()
					lastrestart = today

	else:
		log("Maloja is not running, starting...",module="supervisor")
		if get_settings("UPDATE_AFTER_CRASH"):
			update()
		start()
		lastrestart = today


	time.sleep(60)
