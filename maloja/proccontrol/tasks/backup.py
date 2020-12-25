import tarfile
from datetime import datetime
import glob
import os
from ...globalconf import data_dir
from pathlib import PurePath

from doreah.logging import log


user_files = {
	"minimal":{
		"rules":["*.tsv"],
		"scrobbles":["*.tsv"]
	},
	"full":{
		"clients":["authenticated_machines.tsv"],
		"images":["artists","tracks"],
		"settings":["settings.ini"]
	}
}

def backup(folder,level="full"):
	print(folder)

	selected_files = user_files["minimal"] if level == "minimal" else {**user_files["minimal"], **user_files["full"]}
	real_files = {cat:[] for cat in selected_files}
	for cat in selected_files:
		catfolder = data_dir[cat]
		for g in selected_files[cat]:
			real_files[cat] += glob.glob(catfolder(g))

	log("Creating backup...")


	now = datetime.utcnow()
	timestr = now.strftime("%Y_%m_%d_%H_%M_%S")
	filename = "maloja_backup_" + timestr + ".tar.gz"
	archivefile = os.path.join(folder,filename)
	assert not os.path.exists(archivefile)
	with tarfile.open(name=archivefile,mode="x:gz") as archive:
		for cat in real_files:
			for f in real_files[cat]:
				p = PurePath(f)
				r = p.relative_to(data_dir[cat]())
				archive.add(f,arcname=os.path.join(cat,r))
	log("Backup created!")
