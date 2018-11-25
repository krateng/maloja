import re

def cleanup(artiststr):

	if artiststr == "":
		return []

	artists = [artiststr]
	
	artistsnew = []
	for a in artists:
		artistsnew.append(re.sub(r"(.*) \(ft. (.*)\)",r"\1",a))
		artistsnew.append(re.sub(r"(.*) \(ft. (.*)\)",r"\2",a))
	
	artists = artistsnew
	artistsnew = []
	
	for a in artists:
		artistsnew.append(a.split(" vs. "))
		
	artists = flatten(artistsnew)
	artistsnew = []
	
	for a in artists:
		artistsnew.append(a.split(" vs "))
		
	artists = flatten(artistsnew)
	artistsnew = []
	
	for a in artists:
		artistsnew.append(a.split(" & "))
		
	artists = flatten(artistsnew)
	artistsnew = []
	
	
	for a in artists:
		artistsnew.append(a.split(" ft. "))
		
	artists = flatten(artistsnew)
	artistsnew = []
	
	for a in artists:
		artistsnew.append(a.split(" Ft. "))
		
	artists = flatten(artistsnew)
	artistsnew = []
	
	
	for a in artists:
		artistsnew.append(a.split(" Feat. "))
		
	artists = flatten(artistsnew)
	artistsnew = []
	
	for a in artists:
		artistsnew.append(a.split(" feat. "))
		
	artists = flatten(artistsnew)
	artistsnew = []
	
	
	for a in artists:
		artistsnew.append(a.split(" featuring "))
		
	artists = flatten(artistsnew)
	artistsnew = []
	
	
	for a in artists:
		artistsnew.append(a.split(" Featuring "))
		
	artists = flatten(artistsnew)
	artistsnew = []
	
	for a in artists:
		artistsnew.append(a.split(" ; "))
		
	artists = flatten(artistsnew)
	artistsnew = []
	
	for a in artists:
		artistsnew.append(a.split("; "))
		
	artists = flatten(artistsnew)
	artistsnew = []
	
	for a in artists:
		artistsnew.append(a.split(";"))
		
	artists = flatten(artistsnew)
	artistsnew = []
	
	#if not artists[0] == artiststr:
	#	print(artiststr + " became " + str(artists))
	
	return artists
	
	
def cleantitle(title):
	title = title.replace("[","(").replace("]",")")
	
	title = re.sub(r" \(as made famous by .*?\)","",title)
	title = re.sub(r" \(originally by .*?\)","",title)
	
	return title

def findartistsintitle(title):
	
	truetitle = title
	artists = ""
	
	newtitle = re.sub(r"(.*) \(ft. (.*?)\)",r"\1",title)
	if (title != newtitle):
		artists = re.sub(r"(.*) \(ft. (.*?)\).*",r"\2",title)
		truetitle = newtitle
	
	newtitle = re.sub(r"(.*) \(feat. (.*?)\)",r"\1",title)
	if (title != newtitle):
		artists = re.sub(r"(.*) \(feat. (.*?)\).*",r"\2",title)
		truetitle = newtitle
	
	newtitle = re.sub(r"(.*) \(Feat. (.*?)\)",r"\1",title)
	if (title != newtitle):
		artists = re.sub(r"(.*) \(Feat. (.*?)\).*",r"\2",title)
		truetitle = newtitle
		
	newtitle = re.sub(r"(.*) \(Ft. (.*?)\)",r"\1",title)
	if (title != newtitle):
		artists = re.sub(r"(.*) \(Ft. (.*?)\).*",r"\2",title)
		truetitle = newtitle
		
	newtitle = re.sub(r"(.*) \(Featuring (.*?)\)",r"\1",title)
	if (title != newtitle):
		artists = re.sub(r"(.*) \(Featuring (.*?)\).*",r"\2",title)
		truetitle = newtitle
		
	newtitle = re.sub(r"(.*) \(featuring (.*?)\)",r"\1",title)
	if (title != newtitle):
		artists = re.sub(r"(.*) \(featuring (.*?)\).*",r"\2",title)
		truetitle = newtitle
		
	
	artistlist = cleanup(artists)
	
	return (truetitle,artistlist)
	
def flatten(lis):

	newlist = []
	
	for l in lis:
		if isinstance(l, str):
			newlist.append(l)
		else:
			newlist = newlist + l
			
	return list(set(newlist))
