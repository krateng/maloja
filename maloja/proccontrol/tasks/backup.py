import tarfile
import time
import glob
import os
from ...pkg_global.conf import dir_settings
from pathlib import PurePath

from doreah.logging import log
from doreah.io import col


basic_files = [
	('config',	['rules/*.tsv','settings.ini','apikeys.yml','custom_css/*.css']),
	('state',	['auth/auth.ddb','malojadb.sqlite'])
]
expanded_files = [
	('state',	['images'])
]

def backup(targetfolder=None,include_images=False):

	if targetfolder is None:
		targetfolder = os.getcwd()

	if include_images:
		file_patterns = basic_files + expanded_files
	else:
		file_patterns = basic_files

	real_files = {}
	for category,patterns in file_patterns:
		real_files.setdefault(category,[])
		for pattern in patterns:
			real_files[category] += glob.glob(os.path.join(dir_settings[category],pattern))

	log("Creating backup...")


	timestr = time.strftime("%Y_%m_%d_%H_%M_%S")
	filename = f"maloja_backup_{timestr}.tar.gz"
	outputfile = os.path.join(targetfolder,filename)
	assert not os.path.exists(outputfile)

	with tarfile.open(name=outputfile,mode="x:gz") as archive:
		for category, filelist in real_files.items():
			for f in filelist:
				p = PurePath(f)
				r = p.relative_to(dir_settings[category])
				archive.add(f,arcname=os.path.join(category,r))
	log("Backup created: " + col['yellow'](outputfile))
	return outputfile
