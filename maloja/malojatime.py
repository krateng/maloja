import datetime
from datetime import datetime as dtm
from calendar import monthrange
from os.path import commonprefix
import math


FIRST_SCROBBLE = int(datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).timestamp())

def register_scrobbletime(timestamp):
	global FIRST_SCROBBLE
	if timestamp < FIRST_SCROBBLE:
		FIRST_SCROBBLE = int(timestamp)

def start_of_scrobbling():
	global FIRST_SCROBBLE
	f = datetime.datetime.utcfromtimestamp(FIRST_SCROBBLE)
	return [f.year]

def end_of_scrobbling():
	global FIRST_SCROBBLE
	f = datetime.datetime.now()
	return [f.year]






### EVERYTHING NEW AGAIN

# only for ranges, timestamps are separate

class MRangeDescriptor:

	def __eq__(self,other):
		if not isinstance(other,MRangeDescriptor): return False
		return (self.first_stamp() == other.first_stamp() and self.last_stamp() == other.last_stamp())

	# gives a hashable object that uniquely identifies this time range
	def hashable(self):
		return self.first_stamp(),self.last_stamp()


	def info(self):
		return {
			"fromstring":self.fromstr(),
			"tostr":self.tostr(),
			"uri":self.uri(),
			"fromstamp":self.first_stamp(),
			"tostamp":self.last_stamp(),
			"description":self.desc()
		}

	def __json__(self):
		return {
			"fromstring":self.fromstr(),
			"tostr":self.tostr(),
			"fromstamp":self.first_stamp(),
			"tostamp":self.last_stamp(),
			"description":self.desc()
		}

	def uri(self):
		return "&".join(k + "=" + self.urikeys[k] for k in self.urikeys)

	def unlimited(self):
		return False

	def active(self):
		return (self.last_stamp() > datetime.datetime.utcnow().timestamp())

	# returns the description of the range including buttons to go back and forth
	#def desc_interactive(self,**kwargs):
	#	if self.next(1) is None:
	#		return self.desc(**kwargs)
	#	else:
	#		prevrange = self.next(-1)
	#		nextrange = self.next(1)

# a range that is exactly a gregorian calendar unit (year, month or day)
class MTime(MRangeDescriptor):
	def __init__(self,*ls):
		# in case we want to call with non-unpacked arguments
		if isinstance(ls[0],tuple) or isinstance(ls[0],list):
			ls = ls[0]

		self.tup = tuple(ls)
		self.precision = len(ls)
		self.year = ls[0]
		if len(ls)>1: self.month = ls[1]
		if len(ls)>2: self.day = ls[2]
		dt = [1970,1,1]
		dt[:len(ls)] = ls
		self.dateobject = datetime.date(dt[0],dt[1],dt[2])

	def __str__(self):
		return "/".join(str(part) for part in self.tup)
	def fromstr(self):
		return str(self)
	def tostr(self):
		return str(self)

	# whether we currently live or will ever again live in this range
	def active(self):
		tod = datetime.datetime.utcnow().date()
		if tod.year > self.year: return False
		if self.precision == 1: return True
		if tod.year == self.year:
			if tod.month > self.month: return False
			if self.precision == 2: return True
			if tod.month == self.month:
				if tod.day > self.day: return False

		return True



	def urikeys(self):
		return {"in":str(self)}

	def desc(self,prefix=False):
		if self.precision == 3:
			if prefix:
				return "on " + self.dateobject.strftime("%d. %B %Y")
			else:
				return self.dateobject.strftime("%d. %B %Y")
		if self.precision == 2:
			if prefix:
				return "in " + self.dateobject.strftime("%B %Y")
			else:
				return self.dateobject.strftime("%B %Y")
		if self.precision == 1:
			if prefix:
				return "in " + self.dateobject.strftime("%Y")
			else:
				return self.dateobject.strftime("%Y")

	def informal_desc(self):
		now = datetime.datetime.now(tz=datetime.timezone.utc)
		today = datetime.date(now.year,now.month,now.day)
		if self.precision == 3:
			diff = (today - dateobject).days
			if diff == 0: return "Today"
			if diff == 1: return "Yesterday"
			if diff < 7 and diff > 1: return timeobject.strftime("%A")
		#elif len(t) == 2:
		return self.desc()

	# describes only the parts that are different than another range object
	def contextual_desc(self,other):
		if isinstance(other,MTime):
			relevant = self.desc().split(" ")
			if self.year == other.year:
				relevant.pop()
				if self.precision > 1 and other.precision > 1 and self.month == other.month:
					relevant.pop()
					if self.precision > 2 and other.precision > 2 and self.day == other.day:
						relevant.pop()
			return " ".join(relevant)
		return self.desc()

	# gets object with one higher precision that starts this one
	def start(self):
		if self.precision == 1: return MTime(self.tup + (1,))
		elif self.precision == 2: return MTime(self.tup + (1,))
	# gets object with one higher precision that ends this one
	def end(self):
		if self.precision == 1: return MTime(self.tup + (12,))
		elif self.precision == 2: return MTime(self.tup + (monthrange(self.year,self.month)[1],))

	def first_day(self):
		if self.precision == 3: return self
		else: return self.start().first_day()
	def last_day(self):
		if self.precision == 3: return self
		else: return self.end().last_day()

	def first_stamp(self):
		day = self.first_day().dateobject
		return int(datetime.datetime.combine(day,datetime.time(tzinfo=datetime.timezone.utc)).timestamp())
	def last_stamp(self):
		day = self.last_day().dateobject + datetime.timedelta(days=1)
		return int(datetime.datetime.combine(day,datetime.time(tzinfo=datetime.timezone.utc)).timestamp() - 1)

	# next range of equal length (not exactly same amount of days, but same precision level)
	def next(self,step=1):
		if abs(step) == math.inf: return None
		if self.precision == 1:
			return MTime(self.year + step)
		elif self.precision == 2:
			dt = [self.year,self.month]
			dt[1] += step
			while dt[1] > 12:
				dt[1] -= 12
				dt[0] += 1
			while dt[1] < 1:
				dt[1] += 12
				dt[0] -= 1
			return MTime(*dt)
		elif self.precision == 3:
			dt = self.dateobject
			d = datetime.timedelta(days=step)
			newdate = dt + d
			return MTime(newdate.year,newdate.month,newdate.day)



# a range that is exactly one christian week (starting on sunday)
class MTimeWeek(MRangeDescriptor):
	def __init__(self,year=None,week=None):
		self.year = year
		self.week = week

		# assume the first day of the first week of this year is 1/1
		firstday = datetime.date(year,1,1)
		y,w,d = firstday.chrcalendar()
		if y == self.year:
			firstday -= datetime.timedelta(days=(d-1))
		else:
			firstday += datetime.timedelta(days=8-d)
		# now we know the real first day, add the weeks we need
		firstday = firstday + datetime.timedelta(days=7*(week-1))
		lastday = firstday + datetime.timedelta(days=6)
		# turn them into local overwritten date objects
		self.firstday = datetime.date(firstday.year,firstday.month,firstday.day)
		self.lastday = datetime.date(lastday.year,lastday.month,lastday.day)
		# now check if we're still in the same year
		y,w,_ = self.firstday.chrcalendar()
		self.year,self.week = y,w
		# firstday and lastday are already correct


	def __str__(self):
		return str(self.year) + "/W" + str(self.week)
	def fromstr(self):
		return str(self)
	def tostr(self):
		return str(self)

	# whether we currently live or will ever again live in this range
#	def active(self):
#		tod = datetime.date.today()
#		if tod.year > self.year: return False
#		if tod.year == self.year:
#			if tod.chrcalendar()[1] > self.week: return False
#
#		return True

	def urikeys(self):
		return {"in":str(self)}

	def desc(self,prefix=False):
		if prefix:
			return "in " + "Week " + str(self.week) + " " + str(self.year)
		else:
			return "Week " + str(self.week) + " " + str(self.year)

	def informal_desc(self):
		now = datetime.datetime.now(tz=datetime.timezone.utc)
		if now.year == self.year: return "Week " + str(self.week)
		return self.desc()

	def contextual_desc(self,other):
		if isinstance(other,MTimeWeek):
			if other.year == self.year: return "Week " + str(self.week)
		return self.desc()

	def start(self):
		return self.first_day()
	def end(self):
		return self.last_day()

	def first_day(self):
		return MTime(self.firstday.year,self.firstday.month,self.firstday.day)
	def last_day(self):
		return MTime(self.lastday.year,self.lastday.month,self.lastday.day)

	def first_stamp(self):
		day = self.firstday
		return int(datetime.datetime.combine(day,datetime.time(tzinfo=datetime.timezone.utc)).timestamp())
	def last_stamp(self):
		day = self.lastday + datetime.timedelta(days=1)
		return int(datetime.datetime.combine(day,datetime.time(tzinfo=datetime.timezone.utc)).timestamp() - 1)

	def next(self,step=1):
		if abs(step) == math.inf: return None
		return MTimeWeek(self.year,self.week + step)

# a range that is defined by separate start and end
class MRange(MRangeDescriptor):

	def __init__(self,since=None,to=None):
		since,to = time_pad(since,to)
		self.since = since
		self.to = to
		if isinstance(self.since,MRange): self.since = self.since.start()
		if isinstance(self.to,MRange): self.to = self.to.end()

	def __str__(self):
		return str(self.since) + " - " + str(self.to)
	def fromstr(self):
		return str(self.since)
	def tostr(self):
		return str(self.to)

	# whether we currently live or will ever again live in this range
	def active(self):
		if self.to is None: return True
		return self.to.active()

	def unlimited(self):
		return (self.since is None and self.to is None)

	def urikeys(self):
		keys = {}
		if self.since is not None: keys["since"] = str(self.since)
		if self.to is not None: keys["to"] = str(self.to)
		return keys

	def desc(self,prefix=False):
		if self.since is not None and self.to is not None:
			if prefix:
				return "from " + self.since.contextual_desc(self.to) + " to " + self.to.desc()
			else:
				return self.since.contextual_desc(self.to) + " to " + self.to.desc()
		if self.since is not None and self.to is None:
			return "since " + self.since.desc()
		if self.since is None and self.to is not None:
			return "until " + self.to.desc()
		if self.since is None and self.to is None:
			return ""

	def informal_desc(self):
		# dis gonna be hard
		return "Not implemented"

	def start(self):
		return self.since

	def end(self):
		return self.to

	def first_day(self):
		return self.since.first_day()
	def last_day(self):
		return self.to.last_day()

	def first_stamp(self):
		if self.since is None: return FIRST_SCROBBLE
		else: return self.since.first_stamp()
	def last_stamp(self):
		if self.to is None: return int(datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).timestamp())
		else: return self.to.last_stamp()

	def next(self,step=1):
		if abs(step) == math.inf: return None
		if self.since is None or self.to is None: return None
		# hop from the start element by one until we reach the end element
		diff = 1
		nxt = self.since
		while (nxt != self.to):
			diff += 1
			nxt = nxt.next(step=1)

		newstart = self.since.next(step=diff*step)
		newend = self.to.next(step=diff*step)

		return MRange(newstart,newend)


## test

w = MTimeWeek(2018,40)
d = MTime(2019,4,9)
m = MTime(2019,7)
y = MTime(2020)



def today():
	tod = datetime.datetime.utcnow()
	return MTime(tod.year,tod.month,tod.day)
def thisweek():
	tod = datetime.datetime.utcnow()
	tod = datetime.date(tod.year,tod.month,tod.day)
	y,w,_ = tod.chrcalendar()
	return MTimeWeek(y,w)
def thismonth():
	tod = datetime.datetime.utcnow()
	return MTime(tod.year,tod.month)
def thisyear():
	tod = datetime.datetime.utcnow()
	return MTime(tod.year)
def alltime():
	return MRange(None,None)





def range_desc(r,**kwargs):
	if r is None: return ""
	return r.desc(**kwargs)

def time_str(t):
	obj = time_fix(t)
	return obj.desc()


currenttime_string_representations = (
	(today,["today","day"]),
	(thisweek,["week","thisweek"]),
	(thismonth,["month","thismonth"]),
	(thisyear,["year","thisyear"]),
	(lambda:None,["alltime"])
)
month_string_representations = (
	["january","jan"],
	["february","feb"],
	["march","mar"],
	["april","apr"],
	["may"],
	["june","jun"],
	["july","jul"],
	["august","aug"],
	["september","sep"],
	["october","oct"],
	["november","nov"],
	["december","dec"],
)
weekday_string_representations = (
	["sunday","sun"],
	["monday","mon"],
	["tuesday","tue"],
	["wednesday","wed"],
	["thursday","thu"],
	["friday","fri"],
	["saturday","sat"]
)

def get_last_instance(category,current,target,amount):
	offset = (target-current) % -(amount)
	return category().next(offset)

str_to_time_range = {
	**{s:callable for callable,strlist in currenttime_string_representations for s in strlist},
	**{s:(lambda i=index:get_last_instance(thismonth,dtm.utcnow().month,i,12)) for index,strlist in enumerate(month_string_representations,1) for s in strlist},
	**{s:(lambda i=index:get_last_instance(today,dtm.utcnow().isoweekday()+1%7,i,7)) for index,strlist in enumerate(weekday_string_representations,1) for s in strlist}
}


# converts strings and stuff to objects
def time_fix(t):
	if t is None or isinstance(t,MRangeDescriptor): return t

	if isinstance(t, str):
		t = t.lower()

		if t in str_to_time_range:
			return str_to_time_range[t]()

	if isinstance(t,str): t = t.split("/")
	#if isinstance(t,tuple): t = list(t)
	try:
		t = [int(p) for p in t]
		return MTime(t[:3])
	except:
		pass

	if isinstance(t[1],str) and t[1].startswith("w"):
		try:
			year = int(t[0])
			weeknum = int(t[1][1:])
			return MTimeWeek(year=year,week=weeknum)
		except:
			raise



def get_range_object(since=None,to=None,within=None):

	since,to,within = time_fix(since),time_fix(to),time_fix(within)

	# check if we can simplify
	if since is not None and to is not None and since == to: within = since
	# TODO

	if within is not None:
		return within
	else:
		return MRange(since,to)




# makes times the same precision level
def time_pad(f,t,full=False):

	if f is None or t is None: return f,t

	# week handling
	if isinstance(f,MTimeWeek) and isinstance(t,MTimeWeek):
		if full: return f.start(),t.end()
		else: return f,t
	if not isinstance(f,MTimeWeek) and isinstance(t,MTimeWeek):
		t = t.end()
	if isinstance(f,MTimeWeek) and not isinstance(t,MTimeWeek):
		f = f.start()

	while (f.precision < t.precision) or (full and f.precision < 3):
		f = f.start()
	while (f.precision > t.precision) or (full and t.precision < 3):
		t = t.end()

	return f,t








### TIMESTAMPS

def timestamp_desc(t,short=False):

	if short:
		now = datetime.datetime.now(tz=datetime.timezone.utc)
		difference = int(now.timestamp() - t)

		if difference < 10: return "just now"
		if difference < 60: return str(difference) + " seconds ago"
		difference = int(difference/60)
		if difference < 60: return str(difference) + " minutes ago" if difference>1 else str(difference) + " minute ago"
		difference = int(difference/60)
		if difference < 24: return str(difference) + " hours ago" if difference>1 else str(difference) + " hour ago"
		difference = int(difference/24)
		timeobject = datetime.datetime.utcfromtimestamp(t)
		if difference < 5: return timeobject.strftime("%A")
		if difference < 31: return str(difference) + " days ago" if difference>1 else str(difference) + " day ago"
		if difference < 300 or timeobject.year == now.year: return timeobject.strftime("%B")
		#if difference < 300: return tim.strftime("%B %Y")

		return timeobject.strftime("%Y")
	else:
		timeobject = datetime.datetime.utcfromtimestamp(t)
		return timeobject.strftime("%d. %b %Y %I:%M %p")








def time_stamps(since=None,to=None,within=None,range=None):

	if range is None: range = get_range_object(since=since,to=to,within=within)
	return range.first_stamp(),range.last_stamp()
	#print(range.desc())
#	if (since==None): stamp1 = FIRST_SCROBBLE
#	else: stamp1 = range.first_stamp()
#	if (to==None): stamp2 = int(datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).timestamp())
#	else: stamp2 = range.last_stamp()
#	return stamp1,stamp2
#	if (since==None): stamp1 = FIRST_SCROBBLE
#	else:
#		stamp1 = since1
#		since = time_fix(since)
#		date = [1970,1,1]
#		date[:len(since)] = since
#		stamp1 = int(datetime.datetime(date[0],date[1],date[2],tzinfo=datetime.timezone.utc).timestamp())
#
#	if (to==None): stamp2 = int(datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).timestamp())
#	else:
#		to = time_fix(to)
#		to = _get_next(to)
#		date = [1970,1,1]
#		date[:len(to)] = to
#		stamp2 = int(datetime.datetime(date[0],date[1],date[2],tzinfo=datetime.timezone.utc).timestamp())
#
#
#	return (stamp1,stamp2-1)


def delimit_desc_p(d):
	return delimit_desc(**d)

def delimit_desc(step="month",stepn=1,trail=1):
	txt = ""
	if stepn is not 1: txt += str(stepn) + "-"
	txt += {"year":"Yearly","month":"Monthly","week":"Weekly","day":"Daily"}[step.lower()]
	if trail is math.inf: txt += " Cumulative"
	elif trail is not 1: txt += " Trailing" #we don't need all the info in the title

	return txt




def day_from_timestamp(stamp):
	dt = datetime.datetime.utcfromtimestamp(stamp)
	return MTime(dt.year,dt.month,dt.day)
def month_from_timestamp(stamp):
	dt = datetime.datetime.utcfromtimestamp(stamp)
	return MTime(dt.year,dt.month)
def year_from_timestamp(stamp):
	dt = datetime.datetime.utcfromtimestamp(stamp)
	return MTime(dt.year)
def week_from_timestamp(stamp):
	dt = datetime.datetime.utcfromtimestamp(stamp)
	d = datetime.date(dt.year,dt.month,dt.day)
	y,w,_ = d.chrcalendar()
	return MTimeWeek(y,w)

def from_timestamp(stamp,unit):
	if unit == "day": return day_from_timestamp(stamp)
	if unit == "week": return week_from_timestamp(stamp)
	if unit == "month": return month_from_timestamp(stamp)
	if unit == "year": return year_from_timestamp(stamp)


# since, to and within can accept old notations or objects. timerange can only be a new object.
def ranges(since=None,to=None,within=None,timerange=None,step="month",stepn=1,trail=1,max_=None):

	(firstincluded,lastincluded) = time_stamps(since=since,to=to,within=within,range=timerange)

	d_start = from_timestamp(firstincluded,step)
	d_start = d_start.next(stepn-1) #last part of first included range
	i = 0
	current_end = d_start
	current_start = current_end.next((stepn*trail-1)*-1)
	#ranges = []
	while current_end.first_stamp() < lastincluded and (max_ is None or i < max_):


		if current_start == current_end:
			yield current_start
			#ranges.append(current_start)
		else:
			yield MRange(current_start,current_end)
			#ranges.append(MRange(current_start,current_end))
		current_end = current_end.next(stepn)
		current_start = current_end.next((stepn*trail-1)*-1)

		i += 1

	#return ranges





#def _get_start_of(timestamp,unit):
#	date = datetime.datetime.utcfromtimestamp(timestamp)
#	if unit == "year":
#		#return [date.year,1,1]
#		return [date.year]
#	elif unit == "month":
#		#return [date.year,date.month,1]
#		return [date.year,date.month]
#	elif unit == "day":
#		return [date.year,date.month,date.day]
#	elif unit == "week":
#		change = (date.weekday() + 1) % 7
#		d = datetime.timedelta(days=change)
#		newdate = date - d
#		return [newdate.year,newdate.month,newdate.day]
#
#def _get_next(time,unit="auto",step=1):
#	result = time[:]
#	if unit == "auto":
#		if is_week(time): unit = "week"
#		# see how long the list is, increment by the last specified unit
#		else: unit = [None,"year","month","day"][len(time)]
#	#while len(time) < 3:
#	#	time.append(1)
#
#	if unit == "year":
#		#return [time[0] + step,time[1],time[2]]
#		result[0] += step
#		return result
#	elif unit == "month":
#		#result = [time[0],time[1] + step,time[2]]
#		result[1] += step
#		while result[1] > 12:
#			result[1] -= 12
#			result[0] += 1
#		while result[1] < 1:
#			result[1] += 12
#			result[0] -= 1
#		return result
#	elif unit == "day":
#		dt = datetime.datetime(time[0],time[1],time[2])
#		d = datetime.timedelta(days=step)
#		newdate = dt + d
#		return [newdate.year,newdate.month,newdate.day]
#		#eugh
#	elif unit == "week":
#		return _get_next(time,"day",step * 7)
#
# like _get_next(), but gets the last INCLUDED day / month whatever
#def _get_end(time,unit="auto",step=1):
#	if step == 1:
#		if unit == "auto": return time[:]
#		if unit == "year" and len(time) == 1: return time[:]
#		if unit == "month" and len(time) == 2: return time[:]
#		if unit == "day" and len(time) == 3: return time[:]
#	exc = _get_next(time,unit,step)
#	inc = _get_next(exc,"auto",-1)
#	return inc
#


#def _is_past(date,limit):
#	date_, limit_ = date[:], limit[:]
#	while len(date_) != 3: date_.append(1)
#	while len(limit_) != 3: limit_.append(1)
#	if not date_[0] == limit_[0]:
#		return date_[0] > limit_[0]
#	if not date_[1] == limit_[1]:
#		return date_[1] > limit_[1]
#	return (date_[2] > limit_[2])
##
