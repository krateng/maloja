import re
import os
import csv

from .pkg_global.conf import data_dir, malojaconfig

# need to do this as a class so it can retain loaded settings from file
# apparently this is not true
# I'm dumb
class CleanerAgent:

	def __init__(self):
		self.updateRules()

	def updateRules(self):

		rawrules = []
		for f in os.listdir(data_dir["rules"]()):
			if f.split('.')[-1].lower() != 'tsv': continue
			filepath = data_dir["rules"](f)
			with open(filepath,'r') as filed:
				reader = csv.reader(filed,delimiter="\t")
				rawrules += [[col for col in entry if col] for entry in reader if len(entry)>0 and not entry[0].startswith('#')]


		self.rules_belongtogether = [r[1] for r in rawrules if r[0]=="belongtogether"]
		self.rules_notanartist = [r[1] for r in rawrules if r[0]=="notanartist"]
		self.rules_replacetitle = {r[1].lower():r[2] for r in rawrules if r[0]=="replacetitle"}
		self.rules_replacealbumtitle = {r[1].lower():r[2] for r in rawrules if r[0]=="replacealbumtitle"}
		self.rules_replaceartist = {r[1].lower():r[2] for r in rawrules if r[0]=="replaceartist"}
		self.rules_ignoreartist = [r[1].lower() for r in rawrules if r[0]=="ignoreartist"]
		self.rules_addartists = {r[2].lower():(r[1].lower(),r[3]) for r in rawrules if r[0]=="addartists"}
		self.rules_fixartists = {r[2].lower():r[1] for r in rawrules if r[0]=="fixartists"}
		self.rules_artistintitle = {r[1].lower():r[2] for r in rawrules if r[0]=="artistintitle"}
		#self.rules_regexartist = [[b,c] for [a,b,c,d] in raw if a=="regexartist"]
		#self.rules_regextitle = [[b,c] for [a,b,c,d] in raw if a=="regextitle"]



	def fullclean(self,artist,title):
		artists = self.parseArtists(self.removespecial(artist))
		title = self.parseTitle(self.removespecial(title))
		(title,moreartists) = self.parseTitleForArtists(title)
		artists += moreartists
		if title.lower() in self.rules_addartists:
			reqartists, allartists = self.rules_addartists[title.lower()]
			reqartists = reqartists.split("␟")
			allartists = allartists.split("␟")
			if set(reqartists).issubset({a.lower() for a in artists}):
				artists += allartists
		elif title.lower() in self.rules_fixartists:
			allartists = self.rules_fixartists[title.lower()]
			allartists = allartists.split("␟")
			if len({a.lower() for a in allartists} & {a.lower() for a in artists}) > 0:
				artists = allartists
		artists = list(set(artists))
		artists.sort()

		return (artists,title.strip())

	def removespecial(self,s):
		if isinstance(s,list):
			return [self.removespecial(se) for se in s]
		s = s.replace("\t","").replace("␟","").replace("\n","")
		s = re.sub(" +"," ",s)
		return s


	# if an artist appears in any created rule, we can assume that artist is meant to exist and be spelled like that
	def confirmedReal(self,a):
		confirmed = self.rules_belongtogether + [self.rules_replaceartist[r] for r in self.rules_replaceartist]
		return (a in confirmed)

	#Delimiters used for extra artists, even when in the title field
	#delimiters_feat = ["ft.","ft","feat.","feat","featuring","Ft.","Ft","Feat.","Feat","Featuring"]
	delimiters_feat = malojaconfig["DELIMITERS_FEAT"]
	#Delimiters in informal artist strings, spaces expected around them
	#delimiters = ["vs.","vs","&"]
	delimiters = malojaconfig["DELIMITERS_INFORMAL"]
	#Delimiters used specifically to tag multiple artists when only one tag field is available, no spaces used
	#delimiters_formal = ["; ",";","/"]
	delimiters_formal = malojaconfig["DELIMITERS_FORMAL"]

	def parseArtists(self,a):

		if isinstance(a,list) or isinstance(a,tuple):
			res = [self.parseArtists(art) for art in a]
			return [a for group in res for a in group]

		if a.strip() in malojaconfig["INVALID_ARTISTS"]:
			return []

		if a.strip().lower() in self.rules_ignoreartist:
			return []

		if a.strip() == "":
			return []

		if a.strip() in self.rules_notanartist:
			return []

		if " performing " in a.lower():
			return self.parseArtists(re.split(" [Pp]erforming",a)[0])

		if a.strip() in self.rules_belongtogether:
			return [a.strip()]
		if a.strip().lower() in self.rules_replaceartist:
			return self.rules_replaceartist[a.strip().lower()].split("␟")



		for d in self.delimiters_feat:
			if re.match(r"(.*) [\(\[]" + d + " (.*)[\)\]]",a,flags=re.IGNORECASE) is not None:
				return self.parseArtists(re.sub(r"(.*) [\(\[]" + d + " (.*)[\)\]]",r"\1",a,flags=re.IGNORECASE)) + \
						self.parseArtists(re.sub(r"(.*) [\(\[]" + d + " (.*)[\)\]]",r"\2",a,flags=re.IGNORECASE))



		for d in (self.delimiters_feat + self.delimiters):
			if ((" " + d + " ") in a):
				ls = []
				for i in a.split(" " + d + " "):
					ls += self.parseArtists(i)
				return ls

		for d in self.delimiters_formal:
			if (d in a):
				ls = []
				for i in a.split(d):
					ls += self.parseArtists(i)
				return ls





		return [a.strip()]

	def parseTitle(self,t):
		if t.strip().lower() in self.rules_replacetitle:
			return self.rules_replacetitle[t.strip().lower()]

		t = t.replace("[","(").replace("]",")")

		# we'll leave these matching all bracket types so future changes
		# won't require readaption
		t = re.sub(r" [\(\[]as made famous by .*?[\)\]]","",t)
		t = re.sub(r" [\(\[]originally by .*?[\)\]]","",t)
		t = re.sub(r" [\(\[].*?Remaster.*?[\)\]]","",t)

		for s in malojaconfig["REMOVE_FROM_TITLE"]:
			if s in t:
				t = t.replace(s,"")

		t = t.strip()
		#for p in self.plugin_titleparsers:
		#	t = p(t).strip()
		return t

	def parseTitleForArtists(self,title):
		artists = []
		for delimiter in malojaconfig["DELIMITERS_FEAT"]:
			for pattern in [
				r" [\(\[]" + re.escape(delimiter) + " (.*?)[\)\]]",
				r" - " + re.escape(delimiter) + " (.*)",
				r" " + re.escape(delimiter) + " (.*)"
			]:
				matches = re.finditer(pattern,title,flags=re.IGNORECASE)
				for match in matches:
					title = match.re.sub('',match.string) # Remove matched part
					artists += self.parseArtists(match.group(1)) # Parse matched artist string



		if malojaconfig["PARSE_REMIX_ARTISTS"]:
			for filter in malojaconfig["FILTERS_REMIX"]:
				for pattern in [
					r" [\(\[](.*)" + re.escape(filter) + "[\)\]]", # match remix in brackets
					r" - (.*)" + re.escape(filter) # match remix split with "-"
				]:
					match = re.search(pattern,title,flags=re.IGNORECASE)
					if match:
						# title stays the same
						artists += self.parseArtists(match.group(1))



		for st in self.rules_artistintitle:
			if st in title.lower(): artists += self.rules_artistintitle[st].split("␟")
		return (title,artists)

	def parseAlbumtitle(self,t):
		if t.strip().lower() in self.rules_replacealbumtitle:
			return self.rules_replacealbumtitle[t.strip().lower()]

		t = t.replace("[","(").replace("]",")")

		t = t.strip()
		return t


def flatten(lis):

	newlist = []

	for l in lis:
		if isinstance(l, str):
			newlist.append(l)
		else:
			newlist += l

	return list(set(newlist))
