import re

def fullclean(artist,title):
	artists = parseArtists(removespecial(artist))
	title = parseTitle(removespecial(title))
	(title,moreartists) = parseTitleForArtists(title)
	artists += moreartists
	
	return (list(set(artists)),title)

def removespecial(s):
	return s.replace("\t","").replace("␟","").replace("\n","")


delimiters_feat = ["ft.","ft","feat.","feat","featuring"]			#Delimiters used for extra artists, even when in the title field
delimiters = ["vs.","vs","&"]							#Delimiters in informal titles, spaces expected around them
delimiters_formal = ["; ",";"]							#Delimiters used specifically to tag multiple artists when only one tag field is available, no spaces used


def parseArtists(a):

	if a.strip() == "":
		return []
	
	for d in delimiters_feat:
		if re.match(r"(.*) \(" + d + " (.*)\)",a) is not None:
			return parseArtists(re.sub(r"(.*) \(" + d + " (.*)\)",r"\1",a)) + parseArtists(re.sub(r"(.*) \(" + d + " (.*)\)",r"\2",a))
	
	for d in (delimiters + delimiters_feat):
		if ((" " + d + " ") in a):
			ls = []
			for i in a.split(" " + d + " "):
				ls += parseArtists(i)
			return ls
			
	for d in delimiters_formal:
		if (d in a):
			ls = []
			for i in a.split(d):
				ls += parseArtists(i)
			return ls
		
	
		
	return [a.strip()]

def parseTitle(t):
	t = t.replace("[","(").replace("]",")")
	
	t = re.sub(r" \(as made famous by .*?\)","",t)
	t = re.sub(r" \(originally by .*?\)","",t)
	
	return t

def parseTitleForArtists(t):
	for d in delimiters_feat:
		if re.match(r"(.*) \(" + d + " (.*?)\)",t) is not None:
			(title,artists) = parseTitleForArtists(re.sub(r"(.*) \(" + d + " (.*?)\)",r"\1",t))
			artists += parseArtists(re.sub(r"(.*) \(" + d + " (.*?)\).*",r"\2",t))
			return (title,artists)
	
	return (t,[])
	
def flatten(lis):

	newlist = []
	
	for l in lis:
		if isinstance(l, str):
			newlist.append(l)
		else:
			newlist = newlist + l
			
	return list(set(newlist))
