import pickle
import os

from ._internal import defaultarguments, gopen, doreahconfig

_config = {}

# set configuration
# folder	folder to store log files
def config(folder="storage"):
	global _config
	_config["folder"] = folder


# initial config on import, set everything to default
config()


@defaultarguments(_config,folder="folder")
def save(data,name,folder):

	filename = os.path.join(folder,name + ".gilly")

	fl = gopen(filename,"wb")
	stream = pickle.dumps(data)
	fl.write(stream)
	fl.close()

@defaultarguments(_config,folder="folder")
def load(name,folder):

	filename = os.path.join(folder,name + ".gilly")

	try:
		fl = gopen(filename,"rb")
		ob = pickle.loads(fl.read())
	except: ob = None
	finally:
		fl.close()

	return ob



# now check local configuration file
_config.update(doreahconfig("persistence"))
