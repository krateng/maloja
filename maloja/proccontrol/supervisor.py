#!/usr/bin/env python3
import os

from ..globalconf import malojaconfig

import subprocess
import setproctitle
import signal
from doreah.logging import log


from .control import getInstance


setproctitle.setproctitle("maloja_supervisor")

def start():
	try:
		return subprocess.Popen(
		    ["python3", "-m", "maloja","run"],
		    stdout=subprocess.DEVNULL,
		    stderr=subprocess.DEVNULL,
		)
	except e:
		log("Error starting Maloja: " + str(e),module="supervisor")



while True:
	log("Maloja is not running, starting...",module="supervisor")
	process = start()

	process.wait()
