from datetime import timezone, timedelta, date, time, datetime
from calendar import monthrange
import math
from abc import ABC, abstractmethod

from .pkg_global.conf import malojaconfig


OFFSET = malojaconfig["TIMEZONE"]
TIMEZONE = timezone(timedelta(hours=OFFSET))
UTC = timezone.utc

FIRST_SCROBBLE = int(datetime.utcnow().replace(tzinfo=UTC).timestamp())

def register_scrobbletime(timestamp):
	global FIRST_SCROBBLE
	if timestamp < FIRST_SCROBBLE:
		FIRST_SCROBBLE = int(timestamp)





# Object that represents a contextual time range relevant for displaying chart information
# there is no smaller unit than days
# also, two distinct objects could represent the same timerange
# (e.g. 2019/03 is not the same as 2019/03/01 - 2019/03/31)


# Generic Time Range
class MTRangeGeneric(ABC):

	# despite the above, ranges that refer to the exact same real time range should evaluate as equal
	def __eq__(self,other):
		if not isinstance(other,MTRangeGeneric): return False
		return (self.first_stamp() == other.first_stamp() and self.last_stamp() == other.last_stamp())

	# gives a hashable object that uniquely identifies this time range
	def hashable(self):
		return self.first_stamp(),self.last_stamp()


	def info(self):
		return {**self.__json__(),"uri":self.uri()}

	def __json__(self):
		return {
			"fromstring":self.fromstr(),
			"tostr":self.tostr(),
			"fromstamp":self.first_stamp(),
			"tostamp":self.last_stamp(),
			"description":self.desc()
		}

	def uri(self):
		return "&".join(k + "=" + self.urikeys()[k] for k in self.urikeys())

	def unlimited(self):
		return False

	def timestamps(self):
		return (self.first_stamp(),self.last_stamp())

	# whether we currently live or will ever again live in this range
	def active(self):
		return (self.last_stamp() > datetime.utcnow().timestamp())

	def __contains__(self,timestamp):
		return timestamp >= self.first_stamp() and timestamp <= self.last_stamp()

	@abstractmethod
	def first_stamp(self):
		pass

	@abstractmethod
	def last_stamp(self):
		pass


# Any range that has one defining base unit, whether week, year, etc.
class MTRangeSingular(MTRangeGeneric):
	def fromstr(self):
		return str(self)
	def tostr(self):
		return str(self)

	def urikeys(self):
		return {"in":str(self)}


# a range that is exactly a gregorian calendar unit (year, month or day)
class MTRangeGregorian(MTRangeSingular):
	def __init__(self,*ls):
		# in case we want to call with non-unpacked arguments
		if isinstance(ls[0], (tuple, list)): ls = ls[0]

		self.tup = tuple(ls)
		self.precision = len(ls)

		self.year = ls[0]
		if len(ls)>1: self.month = ls[1]
		if len(ls)>2: self.day = ls[2]
		dt = [1970,1,1]
		dt[:len(ls)] = ls
		self.dateobject = date(dt[0],dt[1],dt[2])

	def __str__(self):
		return "/".join(str(part) for part in self.tup)


	# whether we currently live or will ever again live in this range
# USE GENERIC SUPER METHOD INSTEAD
#	def active(self):
#		tod = datetime.datetime.utcnow().date()
#		if tod.year > self.year: return False
#		if self.precision == 1: return True
#		if tod.year == self.year:
#			if tod.month > self.month: return False
#			if self.precision == 2: return True
#			if tod.month == self.month and tod.day > self.day: return False
#		return True



	def desc(self,prefix=False):
		prefixes = (None,'in ','in ','on ')
		formats = ('%Y','%B','%d')

		timeformat = ' '.join(reversed(formats[0:self.precision]))

		if prefix: return prefixes[self.precision] + self.dateobject.strftime(timeformat)
		else: return self.dateobject.strftime(timeformat)


	def informal_desc(self):
		# TODO: ignore year when same year etc
		now = datetime.now(tz=timezone.utc)
		today = date(now.year,now.month,now.day)
		if self.precision == 3:
			diff = (today - dateobject).days
			if diff == 0: return "Today"
			if diff == 1: return "Yesterday"
			if diff < 7 and diff > 1: return timeobject.strftime("%A")
		#elif len(t) == 2:
		return self.desc()

	# describes only the parts that are different than another range object
	def contextual_desc(self,other):
		# TODO: more elegant maybe?
		if not isinstance(other, MTRangeGregorian): return self.desc()

		relevant = self.desc().split(" ")
		if self.year == other.year:
			relevant.pop()
			if self.precision > 1 and other.precision > 1 and self.month == other.month:
				relevant.pop()
				if self.precision > 2 and other.precision > 2 and self.day == other.day:
					relevant.pop()
		return " ".join(relevant)


	# get objects with one higher precision that start or end this one
	def start(self):
		if self.precision in [1, 2]: return MTRangeGregorian(*self.tup,1)
		return self
	def end(self):
		if self.precision == 1: return MTRangeGregorian(*self.tup,12)
		elif self.precision == 2: return MTRangeGregorian(*self.tup,monthrange(self.year,self.month)[1])
		return self

	# get highest precision objects (day) that start or end this one
	def first_day(self):
		if self.precision == 3: return self
		else: return self.start().first_day()
	def last_day(self):
		if self.precision == 3: return self
		else: return self.end().last_day()

	# get first or last timestamp of this range
	def first_stamp(self):
		day = self.first_day().dateobject
		return int(datetime.combine(day,time(tzinfo=TIMEZONE)).timestamp())
	def last_stamp(self):
		day = self.last_day().dateobject + timedelta(days=1)
		return int(datetime.combine(day,time(tzinfo=TIMEZONE)).timestamp() - 1)

	# next range of equal length (not exactly same amount of days, but same precision level)
	def next(self,step=1):
		if abs(step) == math.inf: return None
		if self.precision == 1:
			return MTRangeGregorian(self.year + step)
		elif self.precision == 2:
			dt = [self.year,self.month]
			dt[1] += step
			while dt[1] > 12:
				dt[1] -= 12
				dt[0] += 1
			while dt[1] < 1:
				dt[1] += 12
				dt[0] -= 1
			return MTRangeGregorian(*dt)
		elif self.precision == 3:
			newdate = self.dateobject + timedelta(days=step)
			return MTRangeGregorian(newdate.year,newdate.month,newdate.day)
	def prev(self,step=1):
		return self.next(step*(-1))



# a range that is exactly one christian week (starting on sunday)
class MTRangeWeek(MTRangeSingular):
	def __init__(self,year=None,week=None):

		# do this so we can construct the week with overflow (eg 2020/-3)
		thisisoyear_firstday = date.fromisocalendar(year,1,1) + timedelta(days=malojaconfig['WEEK_OFFSET']-1)
		self.firstday = thisisoyear_firstday + timedelta(days=7*(week-1))

		self.lastday = self.firstday + timedelta(days=6)

		# now get the actual year and week number (in case of overflow)
		fakedate = self.firstday - timedelta(days=malojaconfig['WEEK_OFFSET']-1)
		# fake date that gives the correct iso return for the real date considering our week offset
		self.year,self.week,_ = fakedate.isocalendar()



	def __str__(self):
		return f"{self.year}/W{self.week}"



	def desc(self,prefix=False):
		if prefix:
			return f"in Week {self.week} {self.year}"
		else:
			return f"Week {self.week} {self.year}"

	def informal_desc(self):
		now = datetime.now(tz=timezone.utc)
		if now.year == self.year: return f"Week {self.week}"
		return self.desc()

	def contextual_desc(self,other):
		if isinstance(other, MTRangeWeek) and other.year == self.year: return f"Week {self.week}"
		return self.desc()

	def start(self):
		return self.first_day()
	def end(self):
		return self.last_day()

	def first_day(self):
		return MTRangeGregorian(self.firstday.year,self.firstday.month,self.firstday.day)
	def last_day(self):
		return MTRangeGregorian(self.lastday.year,self.lastday.month,self.lastday.day)

	def first_stamp(self):
		day = self.firstday
		return int(datetime.combine(day,time(tzinfo=TIMEZONE)).timestamp())
	def last_stamp(self):
		day = self.lastday + timedelta(days=1)
		return int(datetime.combine(day,time(tzinfo=TIMEZONE)).timestamp() - 1)

	def next(self,step=1):
		if abs(step) == math.inf: return None
		return MTRangeWeek(self.year,self.week + step)

# a range that is defined by separate start and end
class MTRangeComposite(MTRangeGeneric):

	def __init__(self,since=None,to=None):
		since,to = time_pad(since,to)
		self.since = since
		self.to = to
		if isinstance(self.since,MTRangeComposite): self.since = self.since.start()
		if isinstance(self.to,MTRangeComposite): self.to = self.to.end()

	def __str__(self):
		return f"{self.since} - {self.to}"
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
				return f"from {self.since.contextual_desc(self.to)} to {self.to.desc()}"
			else:
				return f"{self.since.contextual_desc(self.to)} to {self.to.desc()}"
		if self.since is not None and self.to is None:
			return f"since {self.since.desc()}"
		if self.since is None and self.to is not None:
			return f"until {self.to.desc()}"
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
		#if self.to is None: return int(datetime.utcnow().replace(tzinfo=timezone.utc).timestamp())
		if self.to is None: return today().last_stamp()
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

		return MTRangeComposite(newstart,newend)






def today():
	tod = datetime.now(tz=TIMEZONE)
	return MTRangeGregorian(tod.year,tod.month,tod.day)
def thisweek():
	tod = datetime.now(tz=TIMEZONE)
	tod = date(tod.year,tod.month,tod.day)
	fakedate = tod - timedelta(days=malojaconfig['WEEK_OFFSET']-1)
	# fake date for correct iso representation
	y,w,_ = fakedate.isocalendar()
	return MTRangeWeek(y,w)
def thismonth():
	tod = datetime.now(tz=TIMEZONE)
	return MTRangeGregorian(tod.year,tod.month)
def thisyear():
	tod = datetime.now(tz=TIMEZONE)
	return MTRangeGregorian(tod.year)
def alltime():
	return MTRangeComposite(None,None)





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
	**{s:(lambda i=index:get_last_instance(thismonth,datetime.utcnow().month,i,12)) for index,strlist in enumerate(month_string_representations,1) for s in strlist},
	**{s:(lambda i=index:get_last_instance(today,datetime.utcnow().isoweekday()+1%7,i,7)) for index,strlist in enumerate(weekday_string_representations,1) for s in strlist}
}


# converts strings and stuff to objects
def time_fix(t):
	if t is None or isinstance(t,MTRangeGeneric): return t

	if isinstance(t, str):
		t = t.lower()

		if t in str_to_time_range:
			return str_to_time_range[t]()

	if isinstance(t,str): t = t.split("/")
	#if isinstance(t,tuple): t = list(t)
	try:
		t = [int(p) for p in t]
		return MTRangeGregorian(t[:3])
	except Exception:
		pass

	if isinstance(t[1],str) and t[1].startswith("w"):
		try:
			year = int(t[0])
			weeknum = int(t[1][1:])
			return MTRangeWeek(year=year,week=weeknum)
		except Exception:
			raise



def get_range_object(since=None,to=None,within=None):

	since,to,within = time_fix(since),time_fix(to),time_fix(within)

	# check if we can simplify
	if since is not None and to is not None and since == to: within = since
	# TODO

	if within is not None:
		return within
	else:
		return MTRangeComposite(since,to)




# makes times the same precision level
def time_pad(f,t,full=False):

	if f is None or t is None: return f,t

	# week handling
	if isinstance(f,MTRangeWeek) and isinstance(t,MTRangeWeek):
		if full: return f.start(),t.end()
		else: return f,t
	if not isinstance(f,MTRangeWeek) and isinstance(t,MTRangeWeek):
		t = t.end()
	if isinstance(f,MTRangeWeek) and not isinstance(t,MTRangeWeek):
		f = f.start()

	while (f.precision < t.precision) or (full and f.precision < 3):
		f = f.start()
	while (f.precision > t.precision) or (full and t.precision < 3):
		t = t.end()

	return f,t








### TIMESTAMPS

def timestamp_desc(t,short=False):

	timeobj = datetime.fromtimestamp(t,tz=TIMEZONE)

	if not short: return timeobj.strftime(malojaconfig["TIME_FORMAT"])

	difference = int(datetime.now().timestamp() - t)

	thresholds = (
		(10,"just now"),
		(2*60,f"{difference} seconds ago"),
		(2*60*60,f"{difference/60:.0f} minutes ago"),
		(2*24*60*60,f"{difference/(60*60):.0f} hours ago"),
		(5*24*60*60,f"{timeobj.strftime('%A')}"),
		(31*24*60*60,f"{difference/(60*60*24):.0f} days ago"),
		(12*31*24*60*60,f"{timeobj.strftime('%B')}"),
		(math.inf,f"{timeobj.strftime('%Y')}")
	)

	for t,s in thresholds:
		if difference < t: return s










def time_stamps(since=None,to=None,within=None,range=None):

	if range is None: range = get_range_object(since=since,to=to,within=within)
	return range.first_stamp(),range.last_stamp()



def delimit_desc_p(d):
	return delimit_desc(**d)

def delimit_desc(step="month",stepn=1,trail=1):
	txt = ""
	if stepn != 1: txt += str(stepn) + "-"
	txt += {"year":"Yearly","month":"Monthly","week":"Weekly","day":"Daily"}[step.lower()]
	if trail is math.inf: txt += " Cumulative"
	elif trail != 1: txt += " Trailing" #we don't need all the info in the title

	return txt




def day_from_timestamp(stamp):
	dt = datetime.fromtimestamp(stamp,tz=TIMEZONE)
	return MTRangeGregorian(dt.year,dt.month,dt.day)
def month_from_timestamp(stamp):
	dt = datetime.fromtimestamp(stamp,tz=TIMEZONE)
	return MTRangeGregorian(dt.year,dt.month)
def year_from_timestamp(stamp):
	dt = datetime.fromtimestamp(stamp,tz=TIMEZONE)
	return MTRangeGregorian(dt.year)
def week_from_timestamp(stamp):
	dt = datetime.fromtimestamp(stamp,tz=TIMEZONE)
	d = date(dt.year,dt.month,dt.day)
	fakedate = d - timedelta(days=malojaconfig['WEEK_OFFSET']-1)
	# fake date for correct iso representation
	y,w,_ = fakedate.isocalendar()
	return MTRangeWeek(y,w)

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
			yield MTRangeComposite(current_start,current_end)
			#ranges.append(MTRangeComposite(current_start,current_end))
		current_end = current_end.next(stepn)
		current_start = current_end.next((stepn*trail-1)*-1)

		i += 1

	#return ranges
