import re
from . import utilities
from doreah import tsv, settings
from .globalconf import datadir
import pkg_resources

# need to do this as a class so it can retain loaded settings from file
# apparently this is not true
# I'm dumb
class CleanerAgent:

	def __init__(self):
		self.updateRules()

	def updateRules(self):
		raw = tsv.parse_all(datadir("rules"),"string","string","string","string")
		self.rules_belongtogether = [b for [a,b,c,d] in raw if a=="belongtogether"]
		self.rules_notanartist = [b for [a,b,c,d] in raw if a=="notanartist"]
		self.rules_replacetitle = {b.lower():c for [a,b,c,d] in raw if a=="replacetitle"}
		self.rules_replaceartist = {b.lower():c for [a,b,c,d] in raw if a=="replaceartist"}
		self.rules_ignoreartist = [b.lower() for [a,b,c,d] in raw if a=="ignoreartist"]
		self.rules_addartists = {c.lower():(b.lower(),d) for [a,b,c,d] in raw if a=="addartists"}
		self.rules_fixartists = {c.lower():b for [a,b,c,d] in raw if a=="fixartists"}
		self.rules_artistintitle = {b.lower():c for [a,b,c,d] in raw if a=="artistintitle"}
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
			if set(reqartists).issubset(set(a.lower() for a in artists)):
				artists += allartists
		elif title.lower() in self.rules_fixartists:
			allartists = self.rules_fixartists[title.lower()]
			allartists = allartists.split("␟")
			if len(set(a.lower() for a in allartists) & set(a.lower() for a in artists)) > 0:
				artists = allartists
		artists = list(set(artists))
		artists.sort()

		return (artists,title)

	def removespecial(self,s):
		s = s.replace("\t","").replace("␟","").replace("\n","")
		s = re.sub(" +"," ",s)
		return s


	# if an artist appears in any created rule, we can assume that artist is meant to exist and be spelled like that
	def confirmedReal(self,a):
		confirmed = self.rules_belongtogether + [self.rules_replaceartist[r] for r in self.rules_replaceartist]
		return (a in confirmed)

	#Delimiters used for extra artists, even when in the title field
	delimiters_feat = ["ft.","ft","feat.","feat","featuring","Ft.","Ft","Feat.","Feat","Featuring"]
	#Delimiters in informal artist strings, spaces expected around them
	delimiters = ["vs.","vs","&"]
	#Delimiters used specifically to tag multiple artists when only one tag field is available, no spaces used
	delimiters_formal = ["; ",";","/"]

	def parseArtists(self,a):

		if a.strip() in settings.get_settings("INVALID_ARTISTS"):
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
			if re.match(r"(.*) \(" + d + " (.*)\)",a) is not None:
				return self.parseArtists(re.sub(r"(.*) \(" + d + " (.*)\)",r"\1",a)) + \
						self.parseArtists(re.sub(r"(.*) \(" + d + " (.*)\)",r"\2",a))

		for d in self.delimiters_formal:
			if (d in a):
				ls = []
				for i in a.split(d):
					ls += self.parseArtists(i)
				return ls

		for d in (self.delimiters_feat + self.delimiters):
			if ((" " + d + " ") in a):
				ls = []
				for i in a.split(" " + d + " "):
					ls += self.parseArtists(i)
				return ls





		return [a.strip()]

	def parseTitle(self,t):
		if t.strip().lower() in self.rules_replacetitle:
			return self.rules_replacetitle[t.strip().lower()]

		t = t.replace("[","(").replace("]",")")

		t = re.sub(r" \(as made famous by .*?\)","",t)
		t = re.sub(r" \(originally by .*?\)","",t)
		t = re.sub(r" \(.*?Remaster.*?\)","",t)

		for s in settings.get_settings("REMOVE_FROM_TITLE"):
			if s in t:
				t = t.replace(s,"")

		t = t.strip()
		#for p in self.plugin_titleparsers:
		#	t = p(t).strip()
		return t

	def parseTitleForArtists(self,t):
		for d in self.delimiters_feat:
			if re.match(r"(.*) \(" + d + " (.*?)\)",t) is not None:
				(title,artists) = self.parseTitleForArtists(re.sub(r"(.*) \(" + d + " (.*?)\)",r"\1",t))
				artists += self.parseArtists(re.sub(r"(.*) \(" + d + " (.*?)\).*",r"\2",t))
				return (title,artists)
			if re.match(r"(.*) - " + d + " (.*)",t) is not None:
				(title,artists) = self.parseTitleForArtists(re.sub(r"(.*) - " + d + " (.*)",r"\1",t))
				artists += self.parseArtists(re.sub(r"(.*) - " + d + " (.*).*",r"\2",t))
				return (title,artists)
			if re.match(r"(.*) " + d + " (.*)",t) is not None:
				(title,artists) = self.parseTitleForArtists(re.sub(r"(.*) " + d + " (.*)",r"\1",t))
				artists += self.parseArtists(re.sub(r"(.*) " + d + " (.*).*",r"\2",t))
				return (title,artists)

		artists = []
		for st in self.rules_artistintitle:
			if st in t.lower(): artists += self.rules_artistintitle[st].split("␟")
		return (t,artists)



#this is for all the runtime changes (counting Trouble Maker as HyunA for charts etc)
class CollectorAgent:

	def __init__(self):
		self.updateRules()

	# rules_countas			dict: real artist -> credited artist
	# rules_countas_id		dict: real artist ID -> credited artist ID
	# rules_include			dict: credited artist -> all real artists

	def updateRules(self):
		raw = tsv.parse_all(datadir("rules"),"string","string","string")
		self.rules_countas = {b:c for [a,b,c] in raw if a=="countas"}
		self.rules_countas_id = {}
		self.rules_include = {} #Twice the memory, double the performance!
		# (Yes, we're saving redundant information here, but it's not unelegant if it's within a closed object!)
		for a in self.rules_countas:
			self.rules_include[self.rules_countas[a]] = self.rules_include.setdefault(self.rules_countas[a],[]) + [a]

	# this agent needs to be aware of the current id assignment in the main program
	# unelegant, but the best way i can think of
	def updateIDs(self,artistlist):
		self.rules_countas_id = {artistlist.index(a):artistlist.index(self.rules_countas[a]) for a in self.rules_countas if a in artistlist}
		#self.rules_include_id = {artistlist.index(a):artistlist.index(self.rules_include[a]) for a in self.rules_include}
		#this needs to take lists into account


	# get who is credited for this artist
	def getCredited(self,artist):
		if artist in self.rules_countas:
			return self.rules_countas[artist]
		if artist in self.rules_countas_id:
			return self.rules_countas_id[artist]

		else:
			return artist

	# get all credited artists for the artists given
	def getCreditedList(self,artists):
		updatedArtists = []
		for artist in artists:
			updatedArtists.append(self.getCredited(artist))
		return list(set(updatedArtists))

	# get artists who the given artist is given credit for
	def getAllAssociated(self,artist):
		return self.rules_include.get(artist,[])

	# this function is there to check for artists that we should include in the
	# database even though they never have any scrobble.
	def getAllArtists(self):
		return list(set([self.rules_countas[a] for a in self.rules_countas]))
		# artists that count can be nonexisting (counting HyunA as 4Minute even
		# though 4Minute has never been listened to)
		# but artists that are counted as someone else are only relevant if they
		# exist (so we can preemptively declare lots of rules just in case)
		#return list(set([a for a in self.rules_countas] + [self.rules_countas[a] for a in self.rules_countas]))







def flatten(lis):

	newlist = []

	for l in lis:
		if isinstance(l, str):
			newlist.append(l)
		else:
			newlist = newlist + l

	return list(set(newlist))
