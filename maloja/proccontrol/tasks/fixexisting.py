import os
from ...globalconf import datadir
import re
from ...cleanup import CleanerAgent
from doreah.logging import log
import difflib
import datetime
from .backup import backup

wendigo = CleanerAgent()

exp = r"([0-9]*)(\t+)([^\t]+?)(\t+)([^\t]+)([^\n]*)\n"
#        1       2    3        4    5       6
# groups:
# 1 - timestamp
# 2 - sep
# 3 - artists
# 4 - sep
# 5 - title
# 6 - rest



def fix():

	backup(level="minimal",folder=datadir("backups"))

	now = datetime.datetime.utcnow()
	nowstr = now.strftime("%Y_%m_%d_%H_%M_%S")
	datestr = now.strftime("%Y/%m/%d")
	timestr = now.strftime("%H:%M:%S")

	patchfolder = datadir("logs","dbfix",nowstr)
	os.makedirs(patchfolder)

	#with open(datadir("logs","dbfix",nowstr + ".log"),"a") as logfile:

	log("Fixing database...")
	for filename in os.listdir(datadir("scrobbles")):
		if filename.endswith(".tsv"):
			log("Fix file " + filename)
			filename_new = filename + "_new"

			with open(datadir("scrobbles",filename_new),"w") as newfile:
				with open(datadir("scrobbles",filename),"r") as oldfile:

					for l in oldfile:

						a,t = re.sub(exp,r"\3",l), re.sub(exp,r"\5",l)
						r1,r2,r3 = re.sub(exp,r"\1\2",l),re.sub(exp,r"\4",l),re.sub(exp,r"\6",l)

						a = a.replace("␟",";")

						(al,t) = wendigo.fullclean(a,t)
						a = "␟".join(al)
						newfile.write(r1 + a + r2 + t + r3 + "\n")


			#os.system("diff " + "scrobbles/" + fn + "_new" + " " + "scrobbles/" + fn)
			with open(datadir("scrobbles",filename_new),"r") as newfile, open(datadir("scrobbles",filename),"r") as oldfile:

				diff = difflib.unified_diff(oldfile.read().split("\n"),newfile.read().split("\n"),lineterm="")
				diff = list(diff)

				with open(os.path.join(patchfolder,filename + ".diff"),"w") as patchfile:
					patchfile.write("\n".join(diff))

			os.rename(datadir("scrobbles",filename_new),datadir("scrobbles",filename))


	log("Database fixed!")
