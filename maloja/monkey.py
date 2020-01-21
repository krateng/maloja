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
		return (cal[0],cal[1],cal[2] % 7)


datetime.date = expandeddate
