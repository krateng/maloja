import json
import os
import time

from doreah.io import col

def export(targetfolder=None):

	from ...database.sqldb import get_scrobbles

	if targetfolder is None:
		targetfolder = os.getcwd()

	timestr = time.strftime("%Y_%m_%d_%H_%M_%S")
	filename = f"maloja_export_{timestr}.json"
	outputfile = os.path.join(targetfolder,filename)
	assert not os.path.exists(outputfile)

	data = {'scrobbles':get_scrobbles()}
	with open(outputfile,'w') as outfd:
		json.dump(data,outfd,indent=3)

	print(f"Exported {len(data['scrobbles'])} Scrobbles to {col['yellow'](outputfile)}")
	return outputfile
