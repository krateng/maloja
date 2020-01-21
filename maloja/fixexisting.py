import os
from .globalconf import datadir
import re
from .cleanup import CleanerAgent
from doreah.logging import log
import difflib
import datetime
from .backup import backup

wendigo = CleanerAgent()

exp = r"([0-9]*)(\t+)([^\t]+?)(\t+)([^\t]+)(\t*)([^\t]*)\n"



def fix():

	backup(level="minimal",folder=datadir("backups"))

	now = datetime.datetime.utcnow()
	nowstr = now.strftime("%Y_%m_%d_%H_%M_%S")
	datestr = now.strftime("%Y/%m/%d")
	timestr = now.strftime("%H:%M:%S")

	with open(datadir("logs","dbfix",nowstr + ".log"),"a") as logfile:

		logfile.write("Database fix initiated on " + datestr + " " + timestr + " UTC")
		logfile.write("\n\n")

		for filename in os.listdir(datadir("scrobbles")):
			if filename.endswith(".tsv"):
				filename_new = filename + "_new"

				with open(datadir("scrobbles",filename_new),"w") as newfile:
					with open(datadir("scrobbles",filename),"r") as oldfile:

						for l in oldfile:

							a,t = re.sub(exp,r"\3",l), re.sub(exp,r"\5",l)
							r1,r2,r3 = re.sub(exp,r"\1\2",l),re.sub(exp,r"\4",l),re.sub(exp,r"\6\7",l)

							a = a.replace("␟",";")

							(al,t) = wendigo.fullclean(a,t)
							a = "␟".join(al)
							newfile.write(r1 + a + r2 + t + r3 + "\n")


				#os.system("diff " + "scrobbles/" + fn + "_new" + " " + "scrobbles/" + fn)
				with open(datadir("scrobbles",filename_new),"r") as newfile:
					with open(datadir("scrobbles",filename),"r") as oldfile:

						diff = difflib.unified_diff(oldfile.read().split("\n"),newfile.read().split("\n"),lineterm="")
						diff = list(diff)[2:]
						#log("Diff for scrobbles/" + filename + "".join("\n\t" + d for d in diff),module="fixer")
						output = "Diff for scrobbles/" + filename + "".join("\n\t" + d for d in diff)
						print(output)
						logfile.write(output)
						logfile.write("\n")

				os.rename(datadir("scrobbles",filename_new),datadir("scrobbles",filename))

				with open(datadir("scrobbles",filename + ".rulestate"),"w") as checkfile:
					checkfile.write(wendigo.checksums)
