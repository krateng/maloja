from .. import database_packed
from . import filters

from .. import database, database_packed, malojatime, utilities, malojauri
from doreah import settings
from doreah.regular import repeatdaily

import urllib
import math

# templating
from jinja2 import Environment, PackageLoader, select_autoescape

dbp = database_packed.DB()

jinja_environment = Environment(
	loader=PackageLoader('maloja', "web/jinja"),
	autoescape=select_autoescape(['html', 'xml'])
)


@repeatdaily
def update_jinja_environment():
	global JINJA_CONTEXT

	JINJA_CONTEXT = {
		# maloja
		"db": database,
		"dbp":dbp,
		"malojatime": malojatime,
		"utilities": utilities,
		"mlj_uri": malojauri,
		"settings": settings.get_settings,
		# external
		"urllib": urllib,
		"math":math,
		# config
		"ranges": [
			('day','7 days',malojatime.today().next(-6),'day',7),
			('week','12 weeks',malojatime.thisweek().next(-11),'week',12),
			('month','12 months',malojatime.thismonth().next(-11),'month',12),
			('year','10 years',malojatime.thisyear().next(-9),'year',12)
		],
		"xranges": [
			{"identifier":"day","localisation":"12 days","firstrange":malojatime.today().next(-11),"amount":12},
			{"identifier":"week","localisation":"12 weeks","firstrange":malojatime.thisweek().next(-11),"amount":12},
			{"identifier":"month","localisation":"12 months","firstrange":malojatime.thismonth().next(-11),"amount":12},
			{"identifier":"year","localisation":"12 years","firstrange":malojatime.thisyear().next(-11),"amount":12}
		],
		"xcurrent": [
			{"identifier":"day","localisation":"Today","range":malojatime.today()},
			{"identifier":"week","localisation":"This Week","range":malojatime.thisweek()},
			{"identifier":"month","localisation":"This Month","range":malojatime.thismonth()},
			{"identifier":"year","localisation":"This Year","range":malojatime.thisyear()},
			{"identifier":"alltime","localisation":"All Time","range":malojatime.alltime()}
		],
		"xdelimiters": [
			{"identifier":"daily","replacekeys":{"step":"day","stepn":1},"localisation":"Daily","heavy":True},
			{"identifier":"weekly","replacekeys":{"step":"week","stepn":1},"localisation":"Weekly"},
			{"identifier":"fortnightly","replacekeys":{"step":"week","stepn":2},"localisation":"Fortnightly"},
			{"identifier":"monthly","replacekeys":{"step":"month","stepn":1},"localisation":"Monthly"},
			{"identifier":"quarterly","replacekeys":{"step":"month","stepn":3},"localisation":"Quarterly"},
			{"identifier":"yearly","replacekeys":{"step":"year","stepn":1},"localisation":"Yearly"}
		],
		"xtrails": [
			{"identifier":"standard","replacekeys":{"trail":1},"localisation":"Standard"},
			{"identifier":"trailing","replacekeys":{"trail":2},"localisation":"Trailing"},
			{"identifier":"longtrailing","replacekeys":{"trail":3},"localisation":"Long Trailing"},
			{"identifier":"inert","replacekeys":{"trail":10},"localisation":"Inert","heavy":True},
			{"identifier":"cumulative","replacekeys":{"trail":math.inf},"localisation":"Cumulative","heavy":True}
		]
	}

	jinja_environment.globals.update(JINJA_CONTEXT)

update_jinja_environment()
jinja_environment.filters.update({k:filters.__dict__[k] for k in filters.__dict__ if not k.startswith("__")})

jinja_environment.trim_blocks = True
jinja_environment.lstrip_blocks = True
jinja_environment.strip_trailing_newlines = False
