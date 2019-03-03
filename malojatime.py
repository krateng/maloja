import datetime
from calendar import monthrange
from os.path import commonprefix


FIRST_SCROBBLE = int(datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).timestamp())

def register_scrobbletime(timestamp):
	global FIRST_SCROBBLE
	if timestamp < FIRST_SCROBBLE:
		FIRST_SCROBBLE = int(timestamp)
	




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
	
	# SPECIAL CASE: Weeks only work for SINCE, but let's hope nobody finds out
	if isinstance(t, str) and t.lower() == "week":
		tod = datetime.datetime.utcnow()
		change = (tod.weekday() + 1) % 7
		d = datetime.timedelta(days=change)
		newdate = tod - d
		
		t = [newdate.year,newdate.month,newdate.day]
		

	if isinstance(t,str): t = t.split("/")
	#if isinstance(t,tuple): t = list(t)
	
	t = [int(p) for p in t]
	
	return t[:3]

# makes times the same precision level		
def time_pad(f,t):
	f,t = time_fix(f), time_fix(t)
	while len(f) < len(t):
		if len(f) == 1: f.append(1)
		elif len(f) == 2: f.append(1)
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
		
		nowdate = [1970,1,1]
		nowobject = datetime.datetime.now(tz=datetime.timezone.utc)
		nowdate[:len(t)] = [nowobject.year, nowobject.month, nowobject.day][:len(t)]
		nowobject = datetime.datetime(nowdate[0],nowdate[1],nowdate[2],tzinfo=datetime.timezone.utc)
		if short:
			if len(t) == 3:
				diff = (nowobject - timeobject).days
				if diff == 0: return "Today"
				if diff == 1: return "Yesterday"
				if diff < 7: return timeobject.strftime("%A")
			#elif len(t) == 2:
				
				
		if len(t) == 3: return timeobject.strftime("%d. %B %Y")
		if len(t) == 2: return timeobject.strftime("%B %Y")
		if len(t) == 1: return timeobject.strftime("%Y")
		
def range_desc(since=None,to=None,within=None,short=False):

	# the 'short' var we pass down to some of the time_desc calls is a different one than the one here
	# the function-wide one indicates whether we want the 'in' 'from' etc at the start
	# the other one is if we want exact dates or weekdays etc
	# but we still hand it down because it makes sense


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
				shortsincestr = time_desc(since,short=True)
				tostr = ""
			elif _week(since,to):
				
				sincestr = "in " + _week(since,to)
				shortsincestr = _week(since,to)
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
		
	
	return (stamp1,stamp2)
	
		
		
		
def delimit_desc(step="month",stepn=1,trail=1):
	txt = ""
	if stepn is not 1: txt += _num(stepn) + "-"
	txt += {"year":"Yearly","month":"Monthly","day":"Daily"}[step.lower()]
	#if trail is not 1: txt += " " + _num(trail) + "-Trailing"
	if trail is not 1: txt += " Trailing" #we don't need all the info in the title
	
	return txt
	
	
def _week(since,to):
	if len(since) != 3 or len(to) != 3: return False
	dt_since, dt_to = datetime.datetime(*since,tzinfo=datetime.timezone.utc), datetime.datetime(*to,tzinfo=datetime.timezone.utc)
	if (dt_to - dt_since).days != 6: return False
	if dt_since.weekday() != 6: return False
	
	c = dt_to.isocalendar()[:2]
	return str("Week " + str(c[1]) + " " + str(c[0]))
	
def _num(i):
	names = ["Zero","One","Two","Three","Four","Five","Six","Seven","Eight","Nine","Ten","Eleven","Twelve"]
	if i < len(names): return names[i]
	else: return str(i)
	
	
	
	
	
	
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
		# see how long the list is, increment by the last specified unit
		unit = [None,"year","month","day"][len(time)]
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

