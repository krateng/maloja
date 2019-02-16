import urllib.request
import shutil
import tempfile
import zipfile
import distutils.dir_util
#import os

SOURCE_URL = "https://github.com/krateng/maloja/archive/master.zip"


update()

def update():
	print("Updating Maloja...")
	with urllib.request.urlopen(SOURCE_URL) as response:
		with tempfile.NamedTemporaryFile(delete=True) as tmpfile:
			shutil.copyfileobj(response,tmpfile)
			
			with zipfile.ZipFile(tmpfile.name,"r") as z:
				
				for f in z.namelist():
					print("extracting " + f)
					z.extract(f)
			
			
	
	distutils.dir_util.copy_tree("./maloja-master/","./",verbose=2)
	shutil.rmtree("./maloja-master")
	print("Done!")
