import os

from ._internal import defaultarguments

_config = {}

# set configuration
# defaultextension	files with this extension will be regarded as valid files. can be overwritten per request.
# comments			whether files may include commenting (indicated by #)
# multitab			whether fields can be separated by multiple tabs (this makes empty fields impossible except when trailing)
def config(defaultextension=".tsv",comments=True,multitab=True):
	global _config
	_config["defaultextension"] = defaultextension
	_config["comments"] = comments
	_config["multitab"] = multitab


# initial config on import, set everything to default
config()


@defaultarguments(_config,comments="comments",multitab="multitab")
def parse(filename,*args,comments,multitab):

	if not os.path.exists(filename):
		filename = filename + _config["defaultextension"]

	f = open(filename)

	result = []
	for l in [l for l in f if (not l.startswith("#")) and (not l.strip()=="")]:
		l = l.replace("\n","")

		# if the file allows comments, we need to replace the escape sequence and properly stop parsing for inline comments
		if comments:
			l = l.split("#")[0]
			l = l.replace(r"\num","#")
			l = l.replace(r"\hashtag","#")

		# we either allow multiple tabs, or we don't (in which case empty fields are possible)
		if multitab:
			data = list(filter(None,l.split("\t")))
		else:
			data = list(l.split("\t"))

		entry = [] * len(args)
		for i in range(len(args)):
			if args[i] in ["list","ls","array"]:
				try:
					entry.append(data[i].split("␟"))
				except:
					entry.append([])
			elif args[i] in ["string","str","text"]:
				try:
					entry.append(data[i])
				except:
					entry.append("")
			elif args[i] in ["int","integer","num","number"]:
				try:
					entry.append(int(data[i]))
				except:
					entry.append(0)
			elif args[i] in ["bool","boolean"]:
				try:
					entry.append((data[i].lower() in ["true","yes","1","y"]))
				except:
					entry.append(False)
			else:
				raise TypeError()

		result.append(entry)

	f.close()
	return result

@defaultarguments(_config,extension="defaultextension")
def parse_all(path,*args,extension,**kwargs):

	result = []
	for f in os.listdir(path + "/"):
		if (f.endswith(extension)): # use "" if all files are valid
			result += parse(path + "/" + f,*args,**kwargs)

	return result



def create(filename):

	if not os.path.exists(filename):
		open(filename,"w").close()

@defaultarguments(_config,comments="comments")
def add_entry(filename,a,comments):

	create(filename)
	# remove all tabs and create tab-separated string
	line = "\t".join([str(e).replace("\t"," ") for e in a])

	# replace comment symbol
	if comments: line = line.replace("#",r"\num")

	with open(filename,"a") as f:
		f.write(line + "\n")

@defaultarguments(_config,comments="comments")
def add_entries(filename,al,comments):

	create(filename)

	with open(filename,"a") as f:
		for a in al:
			line = "\t".join([str(e).replace("\t"," ") for e in a])
			if comments: line = line.replace("#",r"\num")
			f.write(line + "\n")
