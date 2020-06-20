#!/usr/bin/env python3
import os

import subprocess
import setproctitle
import signal
from doreah.logging import log
from doreah.settings import get_settings

from .control import getInstance


setproctitle.setproctitle("maloja_supervisor")

def update():
	log("Updating...",module="supervisor")
	try:
		os.system("pip3 install maloja --upgrade --no-cache-dir")
	except:
		log("Could not update.",module="supervisor")

def start():
	try:
		p = subprocess.Popen(["python3","-m","maloja.server"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
		return p
	except e:
		log("Error starting Maloja: " + str(e),module="supervisor")



while True:
	log("Maloja is not running, starting...",module="supervisor")
	if get_settings("UPDATE_AFTER_CRASH"):
		update()
	process = start()

	process.wait()
