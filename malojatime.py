import datetime
from calendar import monthrange


# This is meant to be a time object that is aware of its own precision
# now I know what you're saying
# "This is total overengineering, Jimmy!"
# "Just convert all user input into timestamps right at the entry into the database and only work with those"
# "You can get the range descriptions right at the start as well or even generate them from timestamps with a simple comparison"
# and you are absolutely correct
# but my name isn't Jimmy
# so we're doing objects
class Time():

	precision = 0
	# 0	unused, no information at all, embrace eternity
	# 1	year
	# 2 	month
	# 3	day
	# 4	specified by exact timestamp

	def __init__(self,*time):
		# time can be a int (timestamp), list or string (/-delimited list)
		
		if len(time) == 1:
			time = time[0] #otherwise we will already have a tuple and we can deal with that
			if isinstance(time,int) and time < 10000: time = [time] # if we have a low number, it's not a timestamp, but a year
		
		
		if isinstance(time,str):
			time = time.split("/")
		if isinstance(time,list) or isinstance(time,tuple):
			time = [int(x) for x in time][:3]
			self.precision = len(time)
			if len(time) > 0: self.YEAR = time[0]
			if len(time) > 1: self.MONTH = time[1]
			if len(time) > 2: self.DAY = time[2]
		elif isinstance(time,int):
			self.precision = 4
			self.TIMESTAMP = time
			dt = datetime.datetime.utcfromtimestamp(time)
			self.YEAR, self.MONTH, self.DAY = dt.year, dt.month, dt.day
		
	
	def _array(self):
		if self.precision == 4:
			timeobject = datetime.datetime.utcfromtimestamp(self.TIMESTAMP)
			return [timeobject.year,timeobject.month,timeobject.day]
		if self.precision == 3: return [self.YEAR,self.MONTH,self.DAY]
		if self.precision == 2: return [self.YEAR,self.MONTH]
		if self.precision == 1: return [self.YEAR]
		
		
	def get(self):
		if self.precision == 4: return self.TIMESTAMP
		if self.precision == 3: return [self.YEAR,self.MONTH,self.DAY]
		if self.precision == 2: return [self.YEAR,self.MONTH]
		if self.precision == 1: return [self.YEAR]
		
	def getStartTimestamp(self):
		if self.precision == 4: return self.TIMESTAMP
		else:
			YEAR = self.YEAR if self.precision > 0 else 1970
			MONTH = self.MONTH if self.precision > 1 else 1
			DAY = self.DAY if self.precision > 2 else 1
			return int(datetime.datetime(YEAR,MONTH,DAY,tzinfo=datetime.timezone.utc).timestamp())
		
	def getEndTimestamp(self):
		if self.precision == 4: return self.TIMESTAMP
		else: return self.getNext().getStartTimestamp()-1		
		
	# get next time of the same precision, e.g. next month if month of this time was defined (even if it's 1 or 12)
	def getNext(self,obj=True):
		if self.precision == 4: result = self.TIMESTAMP + 1
		else: result = _getNext(self._array())

		if obj: return Time(result)
		else: return result
		
	
	def pad(self,precision=3):
		arrayA, arrayB = self._array(), self._array()
		if self.precision < min(2,precision):
			arrayA.append(1)
			arrayB.append(12)
		if self.precision+1 < min(3,precision):
			arrayA.append(1)
			arrayB.append(monthrange(*arrayB)[1])
			
		return (arrayA,arrayB)
			
	def describe(self,short=False):
		if self.precision == 4:
			if short:
				now = datetime.datetime.now(tz=datetime.timezone.utc)
				difference = int(now.timestamp() - self.TIMESTAMP)
				
				if difference < 10: return "just now"
				if difference < 60: return str(difference) + " seconds ago"
				difference = int(difference/60)
				if difference < 60: return str(difference) + " minutes ago" if difference>1 else str(difference) + " minute ago"
				difference = int(difference/60)
				if difference < 24: return str(difference) + " hours ago" if difference>1 else str(difference) + " hour ago"
				difference = int(difference/24)
				timeobject = datetime.datetime.utcfromtimestamp(self.TIMESTAMP)
				if difference < 5: return timeobject.strftime("%A")
				if difference < 31: return str(difference) + " days ago" if difference>1 else str(difference) + " day ago"
				#if difference < 300 and tim.year == now.year: return tim.strftime("%B")
				#if difference < 300: return tim.strftime("%B %Y")
				
				return timeobject.strftime("%d. %B %Y")
			else:
				timeobject = datetime.datetime.utcfromtimestamp(self.TIMESTAMP)
				return tim.strftime("%d. %b %Y %I:%M %p")
				
		else:
			YEAR = self.YEAR if self.precision > 0 else 2022
			MONTH = self.MONTH if self.precision > 1 else 5 #else numbers dont matter, just needed to create the datetime object
			DAY = self.DAY if self.precision > 2 else 4
			timeobject = datetime.datetime(YEAR,MONTH,DAY,tzinfo=datetime.timezone.utc)
		if self.precision == 3: return timeobject.strftime("%d. %B %Y")
		if self.precision == 2: return timeobject.strftime("%B %Y")
		if self.precision == 1: return timeobject.strftime("%Y")
		if self.precision == 0: return "Embrace Eternity"
		
	
def getRange(timeA,timeB):
	return (timeA.getStartTimestamp(),timeB.getEndTimestamp())
	
def getRangeDesc(timeA,timeB):
	aA, aB = timeA.get(), timeB.get()
	if len(aA) != len(aB):
		prec = max(len(aA),len(aB))
		aA, aB = timeA.pad(prec)[0], timeB.pad(prec)[1]
	if aA == aB:
		return Time(aA).describe()
	if aA[:-1] == aB[:-1]:
		return " ".join(Time(aA).describe().split(" ")[:-1]) + " to " + Time(aB).describe() #what
	
		
	
	
	
def _getNext(time,unit="auto",step=1):
	result = time[:]
	if unit == "auto":
		# see how long the list is, increment by the last specified unit
		unit = [None,"year","month","day"][len(time)]

	if unit == "year":
		result[0] += step
		return result
	elif unit == "month":
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
		return getNext(time,"day",step * 7)
	
