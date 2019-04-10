import datetime
from calendar import monthrange
from os.path import commonprefix


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



#def uri_to_internal(t):
#	return time_fix(t)
#
#def internal_to_uri(t):
#	if isinstance(t,list) or isinstance(t,tuple):
#		return "/".join(str(t))
#
#	return str(t)


### helpers

# adjusting to sunday-first calendar
# damn iso heathens
class expandeddate(datetime.date):

	def chrweekday(self):
		return self.isoweekday() + 1 % 7

	def chrcalendar(self):
		tomorrow = self + datetime.timedelta(days=1)
		cal = tomorrow.isocalendar()
		return (cal[0],cal[1],cal[2] % 7)

date = expandeddate




### EVERYTHING NEW AGAIN

# only for ranges, timestamps are separate

class MTime:
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
		self.dateobject = date(dt[0],dt[1],dt[2])

	def __str__(self):
		return "/".join(str(part) for part in self.tup)

	def uri(self):
		return "in=" + str(self)

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



class MTimeWeek:
	def __init__(self,year=None,week=None):
		self.year = year
		self.week = week

		firstday = date(year,1,1)
		y,w,d = firstday.chrcalendar()
		if y == self.year:
			firstday -= datetime.timedelta(days=(d-1))
		else:
			firstday += datetime.timedelta(days=8-d)
		self.firstday = firstday + datetime.timedelta(days=7*(week-1))
		self.lastday = self.firstday + datetime.timedelta(days=6)

	def __str__(self):
		return str(self.year) + "/W" + str(self.week)

	def uri(self):
		return "in=" + str(self)

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


class MRange:

	def __init__(self,since=None,to=None):
		since,to = time_pad(since,to)
		self.since = since
		self.to = to

	def __str__(self):
		return str(self.since) + " - " + str(self.to)

	def uri(self):
		keys = []
		if self.since is not None: keys.append("since=" + uri(self.since))
		if self.to is not None: keys.append("&to=" + uri(self.to))
		return "&".join(keys)

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
		return self.since.first_stamp()
	def last_stamp(self):
		return self.to.last_stamp()

## test

w = MTimeWeek(2018,40)
d = MTime(2019,4,9)
m = MTime(2019,7)
y = MTime(2020)




def time_str(t):
	return str(t)

# converts strings and stuff to objects
def time_fix(t):


	if isinstance(t, str):
		tod = datetime.datetime.utcnow()
		months = ["january","february","march","april","may","june","july","august","september","october","november","december"]
		weekdays = ["sunday","monday","tuesday","wednesday","thursday","friday","saturday"]

		if t.lower() in ["today","day"]:
			t = [tod.year,tod.month,tod.day]
		elif t.lower() == "month":
			t = [tod.year,tod.month]
		elif t.lower() == "year":
			t = [tod.year]


		elif t.lower() in months:
			#diff = (tod.month - months.index(t.lower()) - 1)
			month = months.index(t.lower()) + 1
			t = [tod.year,month]
			if month > tod.month: t[0] -= 1
		elif t.lower() in weekdays:
			weekday = weekdays.index(t.lower())
			diff = (tod.isoweekday() - weekday) % 7
			dt = tod - datetime.timedelta(diff)
			t = [dt.year,dt.month,dt.day]

	if isinstance(t,str): t = t.split("/")
	#if isinstance(t,tuple): t = list(t)
	try:
		t = [int(p) for p in t]
		return MTime(t[:3])
	except:
		pass

	if isinstance(t[1],str) and t[1].startswith("W"):
		try:
			weeknum = int(t[1][1:])
			return MTimeWeek(year=t[0],week=t[1])
		except:
			pass





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
		#if difference < 300 and tim.year == now.year: return tim.strftime("%B")
		#if difference < 300: return tim.strftime("%B %Y")

		return timeobject.strftime("%d. %B %Y")
	else:
		timeobject = datetime.datetime.utcfromtimestamp(t)
		return timeobject.strftime("%d. %b %Y %I:%M %p")








def time_stamps(since=None,to=None,within=None):


	if within is not None:
		since = within
		to = within




	if (since==None): stamp1 = FIRST_SCROBBLE
	else:
		since = time_fix(since)
		date = [1970,1,1]
		date[:len(since)] = since
		stamp1 = int(datetime.datetime(date[0],date[1],date[2],tzinfo=datetime.timezone.utc).timestamp())

	if (to==None): stamp2 = int(datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).timestamp())
	else:
		to = time_fix(to)
		to = _get_next(to)
		date = [1970,1,1]
		date[:len(to)] = to
		stamp2 = int(datetime.datetime(date[0],date[1],date[2],tzinfo=datetime.timezone.utc).timestamp())


	return (stamp1,stamp2-1)




def delimit_desc(step="month",stepn=1,trail=1):
	txt = ""
	if stepn is not 1: txt += _num(stepn) + "-"
	txt += {"year":"Yearly","month":"Monthly","day":"Daily"}[step.lower()]
	#if trail is not 1: txt += " " + _num(trail) + "-Trailing"
	if trail is not 1: txt += " Trailing" #we don't need all the info in the title

	return txt




def ranges(since=None,to=None,within=None,step="month",stepn=1,trail=1,max_=None):

	(firstincluded,lastincluded) = time_stamps(since=since,to=to,within=within)

	d_start = _get_start_of(firstincluded,step)
	d_end = _get_start_of(lastincluded,step)
	d_start = _get_next(d_start,step,stepn)			# first range should end right after the first active scrobbling week / month / whatever relevant step
	d_start = _get_next(d_start,step,stepn * trail * -1)	# go one range back to begin


	i = 0
	d_current = d_start
	while not _is_past(d_current,d_end) and (max_ is None or i < max_):
		d_current_end = _get_end(d_current,step,stepn * trail)
		yield (d_current,d_current_end)
		d_current = _get_next(d_current,step,stepn)
		i += 1



def _get_start_of(timestamp,unit):
	date = datetime.datetime.utcfromtimestamp(timestamp)
	if unit == "year":
		#return [date.year,1,1]
		return [date.year]
	elif unit == "month":
		#return [date.year,date.month,1]
		return [date.year,date.month]
	elif unit == "day":
		return [date.year,date.month,date.day]
	elif unit == "week":
		change = (date.weekday() + 1) % 7
		d = datetime.timedelta(days=change)
		newdate = date - d
		return [newdate.year,newdate.month,newdate.day]

def _get_next(time,unit="auto",step=1):
	result = time[:]
	if unit == "auto":
		if is_week(time): unit = "week"
		# see how long the list is, increment by the last specified unit
		else: unit = [None,"year","month","day"][len(time)]
	#while len(time) < 3:
	#	time.append(1)

	if unit == "year":
		#return [time[0] + step,time[1],time[2]]
		result[0] += step
		return result
	elif unit == "month":
		#result = [time[0],time[1] + step,time[2]]
		result[1] += step
		while result[1] > 12:
			result[1] -= 12
			result[0] += 1
		while result[1] < 1:
			result[1] += 12
			result[0] -= 1
		return result
	elif unit == "day":
		dt = datetime.datetime(time[0],time[1],time[2])
		d = datetime.timedelta(days=step)
		newdate = dt + d
		return [newdate.year,newdate.month,newdate.day]
		#eugh
	elif unit == "week":
		return _get_next(time,"day",step * 7)

# like _get_next(), but gets the last INCLUDED day / month whatever
def _get_end(time,unit="auto",step=1):
	if step == 1:
		if unit == "auto": return time[:]
		if unit == "year" and len(time) == 1: return time[:]
		if unit == "month" and len(time) == 2: return time[:]
		if unit == "day" and len(time) == 3: return time[:]
	exc = _get_next(time,unit,step)
	inc = _get_next(exc,"auto",-1)
	return inc



def _is_past(date,limit):
	date_, limit_ = date[:], limit[:]
	while len(date_) != 3: date_.append(1)
	while len(limit_) != 3: limit_.append(1)
	if not date_[0] == limit_[0]:
		return date_[0] > limit_[0]
	if not date_[1] == limit_[1]:
		return date_[1] > limit_[1]
	return (date_[2] > limit_[2])
