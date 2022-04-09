# custom json encoding



def newdefault(self,object):
	return getattr(object.__class__,"__json__", self._olddefault)(object)


# just patch every encoder
try:
	from simplejson import JSONEncoder
	JSONEncoder._olddefault = JSONEncoder.default
	JSONEncoder.default = newdefault
except:
	pass

try:
	from json import JSONEncoder
	JSONEncoder._olddefault = JSONEncoder.default
	JSONEncoder.default = newdefault
except:
	pass

try:
	from ujson import JSONEncoder
	JSONEncoder._olddefault = JSONEncoder.default
	JSONEncoder.default = newdefault
except:
	pass




# proper sunday-first weeks
# damn iso heathens

from datetime import date, timedelta
import datetime

class expandeddate(date):

	def chrweekday(self):
		return self.isoweekday() + 1 % 7

	def chrcalendar(self):
		tomorrow = self + timedelta(days=1)
		cal = tomorrow.isocalendar()
		return (cal[0],cal[1],cal[2])

	@classmethod
	def fromchrcalendar(cls,y,w,d):
		try:
			return datetime.date.fromisocalendar(y,w,d) - timedelta(days=1) #sunday instead of monday
		except:
			# pre python3.8 compatibility

			firstdayofyear = datetime.date(y,1,1)
			wkday = firstdayofyear.isoweekday()
			if wkday <= 4: # day up to thursday -> this week belongs to the new year
				firstisodayofyear = firstdayofyear - timedelta(days=wkday) #this also shifts to sunday-first weeks
			else: # if not, still old year
				firstisodayofyear = firstdayofyear + timedelta(days=7-wkday) #same
			return firstisodayofyear + timedelta(days=(w-1)*7) + timedelta(days=d-1)



datetime.date = expandeddate
