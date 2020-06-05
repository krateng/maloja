import os
from ..lastfmconverter import convert
from ..backup import backup
from ..fixexisting import fix
from ..globalconf import datadir
from .control import restart
from doreah.io import ask

def loadlastfm(filename):

	if not os.path.exists(filename):
		print("File could not be found.")
		return

	if os.path.exists(datadir("scrobbles/lastfmimport.tsv")):
		overwrite = ask("Already imported Last.FM data. Overwrite?",default=False)
		if not overwrite: return
	print("Please wait...")

	convert(filename,datadir("scrobbles/lastfmimport.tsv"))
	#os.system("python3 -m maloja.lastfmconverter " + filename + " " + datadir("scrobbles/lastfmimport.tsv"))
	print("Successfully imported your Last.FM scrobbles!")


def backuphere():
	backup(folder=os.getcwd())

def update():
	os.system("pip3 install malojaserver --upgrade --no-cache-dir")
	restart()

def fixdb():
	fix()
