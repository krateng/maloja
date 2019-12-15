import tarfile
from datetime import datetime
import glob
import os
from .globalconf import datadir


user_files = {
	"minimal":[
		"rules/*.tsv",
		"scrobbles"
	],
	"full":[
		"clients/authenticated_machines.tsv",
		"images/artists",
		"images/tracks",
		"settings/settings.ini"
	]
}

def backup(folder,level="full"):

	selected_files = user_files["minimal"] if level == "minimal" else user_files["minimal"] + user_files["full"]
	real_files = []
	for g in selected_files:
		real_files += glob.glob(datadir(g))

	now = datetime.utcnow()
	timestr = now.strftime("%Y_%m_%d_%H_%M_%S")
	filename = "maloja_backup_" + timestr + ".tar.gz"
	archivefile = os.path.join(folder,filename)
	assert not os.path.exists(archivefile)
	with tarfile.open(name=archivefile,mode="x:gz") as archive:
		for f in real_files:
			archive.add(f)
