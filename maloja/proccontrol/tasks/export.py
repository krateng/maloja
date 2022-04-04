import json
import os
import time

from doreah.io import col

from ...database.sqldb import get_scrobbles

def export(targetfolder="."):

	outputfile = os.path.join(targetfolder,f"maloja_export_{time.strftime('%Y%m%d')}.json")

	data = {'scrobbles':get_scrobbles()}
	with open(outputfile,'w') as outfd:
		json.dump(data,outfd,indent=3)

	print(f"Exported {len(data['scrobbles'])} Scrobbles to {col['yellow'](outputfile)}")
