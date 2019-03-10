import os
import re
from cleanup import CleanerAgent
from utilities import log
import difflib

wendigo = CleanerAgent()

exp = r"([0-9]*)(\t+)([^\t]+?)(\t+)([^\t]+)(\t*)([^\t]*)\n"

for fn in os.listdir("scrobbles/"):
	if fn.endswith(".tsv"):
		f = open("scrobbles/" + fn)
		fnew = open("scrobbles/" + fn + "_new","w")
		for l in f:
			
			a,t = re.sub(exp,r"\3",l), re.sub(exp,r"\5",l)
			r1,r2,r3 = re.sub(exp,r"\1\2",l),re.sub(exp,r"\4",l),re.sub(exp,r"\6\7",l)
			
			a = a.replace("␟",";")
			
			(al,t) = wendigo.fullclean(a,t)
			a = "␟".join(al)
			fnew.write(r1 + a + r2 + t + r3 + "\n")
			
			#print("Artists: " + a)
			#print("Title: " + t)
			#print("1: " + r1)
			#print("2: " + r2)
			#print("3: " + r3)
			
		f.close()
		fnew.close()
		
		#os.system("diff " + "scrobbles/" + fn + "_new" + " " + "scrobbles/" + fn)
		with open("scrobbles/" + fn + "_new","r") as newfile:
			with open("scrobbles/" + fn,"r") as oldfile:
				diff = difflib.unified_diff(oldfile.read().split("\n"),newfile.read().split("\n"),lineterm="")
				diff = list(diff)[2:]
				log("Diff for scrobbles/" + fn + "".join("\n\t" + d for d in diff),module="fixer")
		
		os.rename("scrobbles/" + fn + "_new","scrobbles/" + fn)
		
		checkfile = open("scrobbles/" + fn + ".rulestate","w")
		checkfile.write(wendigo.checksums)
		checkfile.close()
