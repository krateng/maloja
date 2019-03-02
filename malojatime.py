import datetime
from calendar import monthrange
from os.path import commonprefix


FIRST_SCROBBLE = int(datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).timestamp())

def register_scrobbletime(timestamp):
	global FIRST_SCROBBLE
	if timestamp < FIRST_SCROBBLE:
		FIRST_SCROBBLE = int(timestamp)
	

# This is meant to be a time object that is aware of its own precision
# now I know what you're saying
# "This is total overengineering, Jimmy!"
# "Just convert all user input into timestamps right at the entry into the database and only work with those"
# "You can get the range descriptions right at the start as well or even generate them from timestamps with a simple comparison"
# and you are absolutely correct
# but my name isn't Jimmy
# so we're doing objects
#class Time():
#
#	precision = 0
#	# 0	unused, no information at all, embrace eternity
#	# 1	year
#	# 2 	month
#	# 3	day
#	# 4	specified by exact timestamp
#
#	def __init__(self,*time):
#		# time can be a int (timestamp), list or string (/-delimited list)
#		
#		if len(time) == 1:
#			time = time[0] #otherwise we will already have a tuple and we can deal with that
#			if isinstance(time,int) and time < 10000: time = [time] # if we have a low number, it's not a timestamp, but a year
#		
#		
#		if isinstance(time,str):
#			time = time.split("/")
#		if isinstance(time,list) or isinstance(time,tuple):
#			time = [int(x) for x in time][:3]
#			self.precision = len(time)
#			if len(time) > 0: self.YEAR = time[0]
#			if len(time) > 1: self.MONTH = time[1]
#			if len(time) > 2: self.DAY = time[2]
#		elif isinstance(time,int):
#			self.precision = 4
#			self.TIMESTAMP = time
#			dt = datetime.datetime.utcfromtimestamp(time)
#			self.YEAR, self.MONTH, self.DAY = dt.year, dt.month, dt.day
#		
#	
#	def _array(self):
#		if self.precision == 4:
#			timeobject = datetime.datetime.utcfromtimestamp(self.TIMESTAMP)
#			return [timeobject.year,timeobject.month,timeobject.day]
#		if self.precision == 3: return [self.YEAR,self.MONTH,self.DAY]
#		if self.precision == 2: return [self.YEAR,self.MONTH]
#		if self.precision == 1: return [self.YEAR]
#		
#		
#	def get(self):
#		if self.precision == 4: return self.TIMESTAMP
#		if self.precision == 3: return [self.YEAR,self.MONTH,self.DAY]
#		if self.precision == 2: return [self.YEAR,self.MONTH]
#		if self.precision == 1: return [self.YEAR]
#		
#	def getStartTimestamp(self):
#		if self.precision == 4: return self.TIMESTAMP
#		else:
#			YEAR = self.YEAR if self.precision > 0 else 1970
#			MONTH = self.MONTH if self.precision > 1 else 1
#			DAY = self.DAY if self.precision > 2 else 1
#			return int(datetime.datetime(YEAR,MONTH,DAY,tzinfo=datetime.timezone.utc).timestamp())
#		
#	def getEndTimestamp(self):
#		if self.precision == 4: return self.TIMESTAMP
#		else: return self.getNext().getStartTimestamp()-1		
#		
#	# get next time of the same precision, e.g. next month if month of this time was defined (even if it's 1 or 12)
#	def getNext(self,obj=True):
#		if self.precision == 4: result = self.TIMESTAMP + 1
#		else: result = _getNext(self._array())
#
#		if obj: return Time(result)
#		else: return result
#		
#	
#	def pad(self,precision=3):
#		arrayA, arrayB = self._array(), self._array()
#		if self.precision < min(2,precision):
#			arrayA.append(1)
#			arrayB.append(12)
#		if self.precision+1 < min(3,precision):
#			arrayA.append(1)
#			arrayB.append(monthrange(*arrayB)[1])
#			
#		return (arrayA,arrayB)
#			
#	def describe(self,short=False):
#		if self.precision == 4:
#			if short:
#				now = datetime.datetime.now(tz=datetime.timezone.utc)
#				difference = int(now.timestamp() - self.TIMESTAMP)
#				
#				if difference < 10: return "just now"
#				if difference < 60: return str(difference) + " seconds ago"
#				difference = int(difference/60)
#				if difference < 60: return str(difference) + " minutes ago" if difference>1 else str(difference) + " minute ago"
#				difference = int(difference/60)
#				if difference < 24: return str(difference) + " hours ago" if difference>1 else str(difference) + " hour ago"
#				difference = int(difference/24)
#				timeobject = datetime.datetime.utcfromtimestamp(self.TIMESTAMP)
#				if difference < 5: return timeobject.strftime("%A")
#				if difference < 31: return str(difference) + " days ago" if difference>1 else str(difference) + " day ago"
#				#if difference < 300 and tim.year == now.year: return tim.strftime("%B")
#				#if difference < 300: return tim.strftime("%B %Y")
#				
#				return timeobject.strftime("%d. %B %Y")
#			else:
#				timeobject = datetime.datetime.utcfromtimestamp(self.TIMESTAMP)
#				return tim.strftime("%d. %b %Y %I:%M %p")
#				
#		else:
#			YEAR = self.YEAR if self.precision > 0 else 2022
#			MONTH = self.MONTH if self.precision > 1 else 5 #else numbers dont matter, just needed to create the datetime object
#			DAY = self.DAY if self.precision > 2 else 4
#			timeobject = datetime.datetime(YEAR,MONTH,DAY,tzinfo=datetime.timezone.utc)
#		if self.precision == 3: return timeobject.strftime("%d. %B %Y")
#		if self.precision == 2: return timeobject.strftime("%B %Y")
#		if self.precision == 1: return timeobject.strftime("%Y")
#		if self.precision == 0: return "Embrace Eternity"
		
	
#def getRange(timeA,timeB):
#	return (timeA.getStartTimestamp(),timeB.getEndTimestamp())
#	
#def getRangeDesc(timeA,timeB):
#	aA, aB = timeA.get(), timeB.get()
#	if len(aA) != len(aB):
#		prec = max(len(aA),len(aB))
#		aA, aB = timeA.pad(prec)[0], timeB.pad(prec)[1]
#	if aA == aB:
#		return Time(aA).describe()
#	if aA[:-1] == aB[:-1]:
#		return " ".join(Time(aA).describe().split(" ")[:-1]) + " to " + Time(aB).describe() #what
#	
	
	
# alright forget everything I've just told you
# so how bout this:
# we completely ignore times
# all singular times (only used for scrobbles) are only ever expressed in timestamps anyway and remain simple ints
# ranges specified in any kind of list are completely separated from them
# even if you specify the pulse 
# holy feck this is so much better


# converts strings and stuff to lists
def time_fix(t):


	if isinstance(t, str) and t.lower() == "today":
		tod = datetime.datetime.utcnow()
		t = [tod.year,tod.month,tod.day]
	if isinstance(t, str) and t.lower() == "month":
		tod = datetime.datetime.utcnow()
		t = [tod.year,tod.month]
	if isinstance(t, str) and t.lower() == "year":
		tod = datetime.datetime.utcnow()
		t = [tod.year]
		

	if isinstance(t,str): t = t.split("/")
	#if isinstance(t,tuple): t = list(t)
	
	t = [int(p) for p in t]
	
	return t[:3]

# makes times the same precision level		
def time_pad(f,t):
	f,t = time_fix(f), time_fix(t)
	while len(f) < len(t):
		if len(f) == 1: f.append(1)
		elif len(f) == 2:	f.append(1)
	while len(f) > len(t):
		if len(t) == 1: t.append(12)
		elif len(t) == 2: t.append(monthrange(*t)[1])
		
	return (f,t)
		
		
def time_desc(t,short=False):
	if isinstance(t,int):
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
			
	else:
		t = time_fix(t)
		date = [1970,1,1]
		date[:len(t)] = t
		timeobject = datetime.datetime(date[0],date[1],date[2],tzinfo=datetime.timezone.utc)
		if len(t) == 3: return timeobject.strftime("%d. %B %Y")
		if len(t) == 2: return timeobject.strftime("%B %Y")
		if len(t) == 1: return timeobject.strftime("%Y")
		
def range_desc(since=None,to=None,within=None,short=False):

	if within is not None:
		since = within
		to = within
	if since is None:
		sincestr = ""
	if to is None:
		tostr = ""
		
	if isinstance(since,int) and to is None:
		sincestr = "since " + time_desc(since)	
		shortsincestr = sincestr	
	elif isinstance(to,int) and since is None:
		tostr = "up until " + time_desc(to)
	elif isinstance(since,int) and not isinstance(to,int):
		sincestr = "from " + time_desc(since)
		shortsincestr = time_desc(since)
		tostr = "to the end of " + time_desc(to)
	elif isinstance(to,int) and not isinstance(since,int):
		sincestr = "from the start of " + time_desc(since)
		shortsincestr = time_desc(since)
		tostr = "to " + time_desc(to)

#	if isinstance(since,int) and isinstance(to,int): result = "from " + time_desc(since) + " to " + time_desc(to)
#	elif isinstance(since,int): result = "from " + time_desc(since) + " to the end of " + time_desc(to)
#	elif isinstance(to,int): result = "from the start of " + time_desc(since) + " to " + time_desc(to)
	else:
		if since is not None and to is not None:
			since,to = time_pad(since,to)
			if since == to:
				if len(since) == 3:
					sincestr = "on " + time_desc(since)
				else:
					sincestr = "in " + time_desc(since)
				shortsincestr = time_desc(since)
				tostr = ""
			else:
				fparts = time_desc(since).split(" ")
				tparts = time_desc(to).split(" ")
				
				fparts.reverse()
				tparts.reverse()
				
				fparts = fparts[len(commonprefix([fparts,tparts])):]
				
				fparts.reverse()
				tparts.reverse()
				
				sincestr =  "from " + " ".join(fparts)
				shortsincestr = " ".join(fparts)
				tostr = "to " + " ".join(tparts)
			
		else:
			if since is not None:
				sincestr = "since " + time_desc(since)
				shortsincestr = sincestr
			if to is not None:
				tostr = "up until " + time_desc(to)
		
	if short: return shortsincestr + " " + tostr
	else: return sincestr + " " + tostr
	
		
	
	
	
def time_stamps(since=None,to=None,within=None):

	from database import getNext
		
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
		to = getNext(to)
		date = [1970,1,1]
		date[:len(to)] = to
		stamp2 = int(datetime.datetime(date[0],date[1],date[2],tzinfo=datetime.timezone.utc).timestamp())
		
	
	return (stamp1,stamp2)
	
		
		
		
def delimit_desc(step,stepn,trail):
	txt = ""
	if stepn is not 1: txt += _num(stepn) + "-"
	txt += {"year":"Yearly","month":"Monthly","day":"Daily"}[step.lower()]
	#if trail is not 1: txt += " " + _num(trail) + "-Trailing"
	if trail is not 1: txt += " Trailing" #we don't need all the info in the title
	
	return txt
	
	
def _num(i):
	names = ["Zero","One","Two","Three","Four","Five","Six","Seven","Eight","Nine","Ten","Eleven","Twelve"]
	if i < len(names): return names[i]
	else: return str(i)
	
		
#def _getNext(time,unit="auto",step=1):
#	result = time[:]
#	if unit == "auto":
#		# see how long the list is, increment by the last specified unit
#		unit = [None,"year","month","day"][len(time)]
#
#	if unit == "year":
#		result[0] += step
#		return result
#	elif unit == "month":
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
#		return getNext(time,"day",step * 7)
#
