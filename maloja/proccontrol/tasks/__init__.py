import os
from doreah.io import ask

from ...globalconf import datadir



def loadlastfm(filename):

	if not os.path.exists(filename):
		print("File could not be found.")
		return

	if os.path.exists(datadir("scrobbles/lastfmimport.tsv")):
		overwrite = ask("Already imported Last.FM data. Overwrite?",default=False)
		if not overwrite: return
	print("Please wait...")

	from .lastfmconverter import convert
	convert(filename,datadir("scrobbles/lastfmimport.tsv"))
	#os.system("python3 -m maloja.lastfmconverter " + filename + " " + datadir("scrobbles/lastfmimport.tsv"))
	print("Successfully imported your Last.FM scrobbles!")


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
