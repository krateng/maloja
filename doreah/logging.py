import datetime
import inspect
import os

from ._internal import defaultarguments, gopen, doreahconfig

_config = {}

_queue = []
_locked = False

# set configuration
# logfolder			folder to store logfiles in
# timeformat		strftime format for log files
# defaultmodule		name for the main running script
# verbosity			higher means more (less important) messages are shown on console
def config(logfolder="logs",timeformat="%Y/%m/%d %H:%M:%S",defaultmodule="main",verbosity=0):
	global _config
	_config["logfolder"] = logfolder
	_config["timeformat"] = timeformat
	_config["defaultmodule"] = defaultmodule
	_config["verbosity"] = verbosity


# initial config on import, set everything to default
config()






# Log entry
# module		allows discrimination between modules of a program. Will be prepended in console output and will determine the separate file for disk storage
# 				defaults to actual name of the calling module or "main" for the main script
# header		determines the hierarchical position of the entry.
# indent		adds indent to the log entry
# importance	low means important. if higher than the configured verbosity, entry will not be shown on console
def log(*msgs,module=None,header=None,indent=0,importance=0):

	now = datetime.datetime.utcnow().strftime(_config["timeformat"])

	# log() can be used to add empty line
	if len(msgs) == 0: msgs = ("",)

	# make it easier to log data structures and such
	msgs = tuple([str(msg) for msg in msgs])

	# header formating
	if header == 2:
		msgs = ("","","####") + msgs + ("####","")
	elif header == 1:
		msgs = ("","","","# # # # #","") + msgs + ("","# # # # #","","")

	# indent
	prefix = "\t" * indent

	# module name
	if module is None:
		try:
			module = inspect.getmodule(inspect.stack()[1][0]).__name__
			if module == "__main__": module = _config["defaultmodule"]
		except:
			module = "interpreter"

	global _locked, _queue
	if _locked:
		for msg in msgs:
			_queue.append({"time":now,"prefix":prefix,"msg":msg,"module":module,"console":(importance <= _config["verbosity"])})
	else:
		# console output
		if (importance <= _config["verbosity"]):
			for msg in msgs:
				print("[" + module + "] " + prefix + msg)

		# file output
		logfilename = _config["logfolder"] + "/" + module + ".log"
		#os.makedirs(os.path.dirname(logfilename), exist_ok=True)
		with gopen(logfilename,"a") as logfile:
			for msg in msgs:
				logfile.write(now + "  " + prefix + msg + "\n")


def flush():
	global _queue
	for entry in _queue:
		# console output
		if entry["console"]:
			print("[" + entry["module"] + "] " + entry["prefix"] + entry["msg"])

		# file output
		logfilename = _config["logfolder"] + "/" + entry["module"] + ".log"
		#os.makedirs(os.path.dirname(logfilename), exist_ok=True)
		with gopen(logfilename,"a") as logfile:
			logfile.write(entry["time"] + "  " + entry["prefix"] + entry["msg"] + "\n")

	_queue = []

# Quicker way to add header
def logh1(*args,**kwargs):
	return log(*args,**kwargs,header=1)
def logh2(*args,**kwargs):
	return log(*args,**kwargs,header=2)




# now check local configuration file
_config.update(doreahconfig("logging"))
