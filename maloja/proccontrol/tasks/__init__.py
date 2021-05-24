import os
from doreah.io import ask,col

from ...globalconf import data_dir



def loadlastfm(filename):

	if not os.path.exists(filename):
		print("File could not be found.")
		return

	if os.path.exists(data_dir['scrobbles']("lastfmimport.tsv")):
		overwrite = ask("Already imported Last.FM data. Overwrite?",default=False)
		if not overwrite: return
	print("Please wait...")

	from .lastfmconverter import convert
	imported,failed = convert(filename,data_dir['scrobbles']("lastfmimport.tsv"))
	print("Successfully imported",imported,"Last.FM scrobbles!")
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
