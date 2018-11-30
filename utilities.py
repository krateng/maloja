


def parseTSV(filename,*args):
	f = open(filename)
	
	result = []
	for l in [l for l in f if (not l.startswith("#")) and (not l.strip()=="")]:
		
		l = l.replace("\n","").split("#")[0]
		data = list(filter(None,l.split("\t"))) # Multiple tabs are okay, we don't accept empty fields unless trailing
		entry = [] * len(args)
		for i in range(len(args)):
			if args[i]=="list":
				try:
					entry.append(data[i].split("␟"))
				except:
					entry.append([])
			elif args[i]=="string":
				try:
					entry.append(data[i])
				except:
					entry.append("")
			elif args[i]=="int":
				try:
					entry.append(int(data[i]))
				except:
					entry.append(0)
			elif args[i]=="bool":
				try:
					entry.append((data[i].lower() in ["true","yes","1","y"]))
				except:
					entry.append(False)
				
		result.append(entry)
		
	f.close()
	return result
	
def parseAllTSV(path,*args):
	
	import os
	
	result = []
	for f in os.listdir(path + "/"):
		
		if (".tsv" in f):
			
			result += parseTSV(path + "/" + f,*args)
			
	return result
	
def createTSV(filename):
	import os
	
	if not os.path.exists(filename):
		open(filename,"w").close()
	
