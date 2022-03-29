import os
from doreah.io import ask,col

from ...globalconf import data_dir



def loadexternal(filename):

	if not os.path.exists(filename):
		print("File could not be found.")
		return

	from .importer import import_scrobbles
	imported,failed,warning = import_scrobbles(filename)
	print("Successfully imported",imported,"scrobbles!")
	if warning > 0:
		print(col['orange'](str(warning) + " Warnings!"))
	if failed > 0:
		print(col['red'](str(failed) + " Errors!"))

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
