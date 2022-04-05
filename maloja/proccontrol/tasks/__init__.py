import os
from doreah.io import ask,col

from ...globalconf import data_dir



def loadexternal(filename):

	if not os.path.exists(filename):
		print("File could not be found.")
		return

	from .import_scrobbles import import_scrobbles
	result = import_scrobbles(filename)

	msg = f"Successfully imported {result['CONFIDENT_IMPORT'] + result['UNCERTAIN_IMPORT']} scrobbles"
	if result['UNCERTAIN_IMPORT'] > 0:
		warningmsg = col['orange'](f"{result['UNCERTAIN_IMPORT']} Warning{'s' if result['UNCERTAIN_IMPORT'] != 1 else ''}!")
		msg += f" ({warningmsg})"
	print(msg)

	msg = f"Skipped {result['CONFIDENT_SKIP'] + result['UNCERTAIN_SKIP']} scrobbles"
	if result['UNCERTAIN_SKIP'] > 0:
		warningmsg = col['indianred'](f"{result['UNCERTAIN_SKIP']} Warning{'s' if result['UNCERTAIN_SKIP'] != 1 else ''}!")
		msg += f" ({warningmsg})"
	print(msg)

	if result['FAIL'] > 0:
		print(col['red'](f"{result['FAIL']} Error{'s' if result['FAIL'] != 1 else ''}!"))

def backuphere():
	from .backup import backup
	backup(folder=os.getcwd())

def update():
	os.system("pip3 install malojaserver --upgrade --no-cache-dir")
	from ..control import restart
	restart()

def fixdb():
	from .fixexisting import fix
	fix()

def generate_scrobbles():
	targetfile = data_dir['scrobbles']("randomgenerated.tsv")

	from .generate import generate
	generate(targetfile)
