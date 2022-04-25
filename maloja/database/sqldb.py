import sqlalchemy as sql
import json
import unicodedata
import math
from datetime import datetime
from threading import Lock

from ..pkg_global.conf import data_dir
from .dbcache import cached_wrapper, cached_wrapper_individual
from . import exceptions as exc

from doreah.logging import log
from doreah.regular import runhourly, runmonthly



##### DB Technical


DBTABLES = {
	# name - type - foreign key - kwargs
	'scrobbles':{
		'columns':[
			("timestamp",       sql.Integer,                                  {'primary_key':True}),
			("rawscrobble",     sql.String,                                   {}),
			("origin",          sql.String,                                   {}),
			("duration",        sql.Integer,                                  {}),
			("track_id",        sql.Integer, sql.ForeignKey('tracks.id'),     {}),
			("extra",           sql.String,                                   {})
		],
		'extraargs':(),'extrakwargs':{}
	},
	'tracks':{
		'columns':[
			("id",              sql.Integer,                                  {'primary_key':True}),
			("title",           sql.String,                                   {}),
			("title_normalized",sql.String,                                   {}),
			("length",          sql.Integer,                                  {})
		],
		'extraargs':(),'extrakwargs':{'sqlite_autoincrement':True}
	},
	'artists':{
		'columns':[
			("id",              sql.Integer,                                  {'primary_key':True}),
			("name",            sql.String,                                   {}),
			("name_normalized", sql.String,                                   {})
		],
		'extraargs':(),'extrakwargs':{'sqlite_autoincrement':True}
	},
	'trackartists':{
		'columns':[
			("id",              sql.Integer,                                  {'primary_key':True}),
			("artist_id",       sql.Integer, sql.ForeignKey('artists.id'),    {}),
			("track_id",        sql.Integer, sql.ForeignKey('tracks.id'),     {})
		],
		'extraargs':(sql.UniqueConstraint('artist_id', 'track_id'),),'extrakwargs':{}
	},
	'associated_artists':{
		'columns':[
			("source_artist",   sql.Integer, sql.ForeignKey('artists.id'),    {}),
			("target_artist",   sql.Integer, sql.ForeignKey('artists.id'),    {})
		],
		'extraargs':(sql.UniqueConstraint('source_artist', 'target_artist'),),'extrakwargs':{}
	}
}




DB = {}

engine = sql.create_engine(f"sqlite:///{data_dir['scrobbles']('malojadb.sqlite')}", echo = False)
meta = sql.MetaData()

# create table definitions
for tablename in DBTABLES:

	DB[tablename] = sql.Table(
		tablename, meta,
		*[sql.Column(colname,*args,**kwargs) for colname,*args,kwargs in DBTABLES[tablename]['columns']],
		*DBTABLES[tablename]['extraargs'],
		**DBTABLES[tablename]['extrakwargs']
	)

# actually create tables for new databases
meta.create_all(engine)

# upgrade old database with new columns
with engine.begin() as conn:
	for tablename in DBTABLES:
		info = DBTABLES[tablename]
		table = DB[tablename]

		for colname,datatype,*args,kwargs in info['columns']:
			try:
				statement = f"ALTER TABLE {tablename} ADD {colname} {datatype().compile()}"
				conn.execute(sql.text(statement))
				log(f"Column {colname} was added to table {tablename}!")
				# TODO figure out how to compile foreign key references!
			except sql.exc.OperationalError as e:
				pass


# adding a scrobble could consist of multiple write operations that sqlite doesn't
# see as belonging together
SCROBBLE_LOCK = Lock()


# decorator that passes either the provided dbconn, or creates a separate one
# just for this function call
def connection_provider(func):

	def wrapper(*args,**kwargs):
		if kwargs.get("dbconn") is not None:
			return func(*args,**kwargs)
		else:
			with engine.connect() as connection:
				with connection.begin():
					kwargs['dbconn'] = connection
					return func(*args,**kwargs)

	wrapper.__innerfunc__ = func
	return wrapper

##### DB <-> Dict translations

## ATTENTION ALL ADVENTURERS
## this is what a scrobble dict will look like from now on
## this is the single canonical source of truth
## stop making different little dicts in every single function
## this is the schema that will definitely 100% stay like this and not
## randomly get changed two versions later
## here we go
#
# {
# 	"time":int,
# 	"track":{
# 		"artists":list,
# 		"title":string,
# 		"album":{
# 			"name":string,
# 			"artists":list
# 		},
# 		"length":None
# 	},
# 	"duration":int,
# 	"origin":string,
#	"extra":{string-keyed mapping for all flags with the scrobble},
#	"rawscrobble":{string-keyed mapping of the original scrobble received}
# }
#
# The last two fields are not returned under normal circumstances




##### Conversions between DB and dicts

# These should work on whole lists and collect all the references,
# then look them up once and fill them in


### DB -> DICT
def scrobbles_db_to_dict(rows,include_internal=False,dbconn=None):
	tracks = get_tracks_map(set(row.track_id for row in rows),dbconn=dbconn)
	return [
		{
			**{
				"time":row.timestamp,
				"track":tracks[row.track_id],
				"duration":row.duration,
				"origin":row.origin,
			},
			**({
				"extra":json.loads(row.extra or '{}'),
				"rawscrobble":json.loads(row.rawscrobble or '{}')
			} if include_internal else {})
		}

		for row in rows
	]

def scrobble_db_to_dict(row,dbconn=None):
	return scrobbles_db_to_dict([row],dbconn=dbconn)[0]

def tracks_db_to_dict(rows,dbconn=None):
	artists = get_artists_of_tracks(set(row.id for row in rows),dbconn=dbconn)
	return [
		{
			"artists":artists[row.id],
			"title":row.title,
			#"album":
			"length":row.length
		}
		for row in rows
	]

def track_db_to_dict(row,dbconn=None):
	return tracks_db_to_dict([row],dbconn=dbconn)[0]

def artists_db_to_dict(rows,dbconn=None):
	return [
		row.name
		for row in rows
	]

def artist_db_to_dict(row,dbconn=None):
	return artists_db_to_dict([row],dbconn=dbconn)[0]




### DICT -> DB
# These should return None when no data is in the dict so they can be used for update statements

def scrobble_dict_to_db(info,dbconn=None):
	return {
		"timestamp":info.get('time'),
		"origin":info.get('origin'),
		"duration":info.get('duration'),
		"track_id":get_track_id(info.get('track'),dbconn=dbconn),
		"extra":json.dumps(info.get('extra')) if info.get('extra') else None,
		"rawscrobble":json.dumps(info.get('rawscrobble')) if info.get('rawscrobble') else None
	}

def track_dict_to_db(info,dbconn=None):
	return {
		"title":info.get('title'),
		"title_normalized":normalize_name(info.get('title','')) or None,
		"length":info.get('length')
	}

def artist_dict_to_db(info,dbconn=None):
	return {
		"name": info,
		"name_normalized":normalize_name(info)
	}





##### Actual Database interactions


@connection_provider
def add_scrobble(scrobbledict,dbconn=None):
	add_scrobbles([scrobbledict],dbconn=dbconn)

@connection_provider
def add_scrobbles(scrobbleslist,dbconn=None):

	with SCROBBLE_LOCK:

		ops = [
			DB['scrobbles'].insert().values(
				**scrobble_dict_to_db(s,dbconn=dbconn)
			) for s in scrobbleslist
		]

		success,errors = 0,0
		for op in ops:
			try:
				dbconn.execute(op)
				success += 1
			except sql.exc.IntegrityError as e:
				errors += 1

				# TODO check if actual duplicate

	if errors > 0: log(f"{errors} Scrobbles have not been written to database!",color='red')
	return success,errors

@connection_provider
def delete_scrobble(scrobble_id,dbconn=None):

	with SCROBBLE_LOCK:

		op = DB['scrobbles'].delete().where(
			DB['scrobbles'].c.timestamp == scrobble_id
		)

		result = dbconn.execute(op)

	return True


### these will 'get' the ID of an entity, creating it if necessary

@cached_wrapper
@connection_provider
def get_track_id(trackdict,create_new=True,dbconn=None):
	ntitle = normalize_name(trackdict['title'])
	artist_ids = [get_artist_id(a,dbconn=dbconn) for a in trackdict['artists']]
	artist_ids = list(set(artist_ids))




	op = DB['tracks'].select(
		DB['tracks'].c.id
	).where(
		DB['tracks'].c.title_normalized==ntitle
	)
	result = dbconn.execute(op).all()
	for row in result:
		# check if the artists are the same
		foundtrackartists = []

		op = DB['trackartists'].select(
			DB['trackartists'].c.artist_id
		).where(
			DB['trackartists'].c.track_id==row[0]
		)
		result = dbconn.execute(op).all()
		match_artist_ids = [r.artist_id for r in result]
		#print("required artists",artist_ids,"this match",match_artist_ids)
		if set(artist_ids) == set(match_artist_ids):
			#print("ID for",trackdict['title'],"was",row[0])
			return row.id

	if not create_new: return None


	op = DB['tracks'].insert().values(
		**track_dict_to_db(trackdict,dbconn=dbconn)
	)
	result = dbconn.execute(op)
	track_id = result.inserted_primary_key[0]

	for artist_id in artist_ids:
		op = DB['trackartists'].insert().values(
			track_id=track_id,
			artist_id=artist_id
		)
		result = dbconn.execute(op)
	#print("Created",trackdict['title'],track_id)
	return track_id

@cached_wrapper
@connection_provider
def get_artist_id(artistname,create_new=True,dbconn=None):
	nname = normalize_name(artistname)
	#print("looking for",nname)

	op = DB['artists'].select(
		DB['artists'].c.id
	).where(
		DB['artists'].c.name_normalized==nname
	)
	result = dbconn.execute(op).all()
	for row in result:
		#print("ID for",artistname,"was",row[0])
		return row.id

	if not create_new: return None

	op = DB['artists'].insert().values(
		name=artistname,
		name_normalized=nname
	)
	result = dbconn.execute(op)
	#print("Created",artistname,result.inserted_primary_key)
	return result.inserted_primary_key[0]


### Edit existing


@connection_provider
def edit_scrobble(scrobble_id,scrobbleupdatedict,dbconn=None):

	dbentry = scrobble_dict_to_db(scrobbleupdatedict,dbconn=dbconn)
	dbentry = {k:v for k,v in dbentry.items() if v}

	print("Updating scrobble",dbentry)

	with SCROBBLE_LOCK:

		op = DB['scrobbles'].update().where(
			DB['scrobbles'].c.timestamp == scrobble_id
		).values(
			**dbentry
		)

		dbconn.execute(op)


@connection_provider
def edit_artist(id,artistupdatedict,dbconn=None):

	artist = get_artist(id)
	changedartist = artistupdatedict # well

	dbentry = artist_dict_to_db(artistupdatedict,dbconn=dbconn)
	dbentry = {k:v for k,v in dbentry.items() if v}

	existing_artist_id = get_artist_id(changedartist,create_new=False,dbconn=dbconn)
	if existing_artist_id not in (None,id):
		raise exc.ArtistExists(changedartist)

	op = DB['artists'].update().where(
		DB['artists'].c.id==id
	).values(
		**dbentry
	)
	result = dbconn.execute(op)

	return True

@connection_provider
def edit_track(id,trackupdatedict,dbconn=None):

	track = get_track(id,dbconn=dbconn)
	changedtrack = {**track,**trackupdatedict}

	dbentry = track_dict_to_db(trackupdatedict,dbconn=dbconn)
	dbentry = {k:v for k,v in dbentry.items() if v}

	existing_track_id = get_track_id(changedtrack,create_new=False,dbconn=dbconn)
	if existing_track_id not in (None,id):
		raise exc.TrackExists(changedtrack)

	op = DB['tracks'].update().where(
		DB['tracks'].c.id==id
	).values(
		**dbentry
	)
	result = dbconn.execute(op)

	return True


### Merge

@connection_provider
def merge_tracks(target_id,source_ids,dbconn=None):

	op = DB['scrobbles'].update().where(
		DB['scrobbles'].c.track_id.in_(source_ids)
	).values(
		track_id=target_id
	)
	result = dbconn.execute(op)
	clean_db(dbconn=dbconn)

	return True

@connection_provider
def merge_artists(target_id,source_ids,dbconn=None):

	# some tracks could already have multiple of the to be merged artists

	# find literally all tracksartist entries that have any of the artists involved
	op = DB['trackartists'].select().where(
		DB['trackartists'].c.artist_id.in_(source_ids + [target_id])
	)
	result = dbconn.execute(op)

	track_ids = set(row.track_id for row in result)

	# now just delete them all lmao
	op = DB['trackartists'].delete().where(
		#DB['trackartists'].c.track_id.in_(track_ids),
		DB['trackartists'].c.artist_id.in_(source_ids + [target_id]),
	)

	result = dbconn.execute(op)

	# now add back the real new artist
	op = DB['trackartists'].insert().values([
		{'track_id':track_id,'artist_id':target_id}
		for track_id in track_ids
	])

	result = dbconn.execute(op)

#	tracks_artists = {}
#	for row in result:
#		tracks_artists.setdefault(row.track_id,[]).append(row.artist_id)
#
#	multiple = {k:v for k,v in tracks_artists.items() if len(v) > 1}
#
#	print([(get_track(k),[get_artist(a) for a in v]) for k,v in multiple.items()])
#
#	op = DB['trackartists'].update().where(
#		DB['trackartists'].c.artist_id.in_(source_ids)
#	).values(
#		artist_id=target_id
#	)
#	result = dbconn.execute(op)

	# this could have created duplicate tracks
	merge_duplicate_tracks(artist_id=target_id,dbconn=dbconn)
	clean_db(dbconn=dbconn)

	return True



### Functions that get rows according to parameters

@cached_wrapper
@connection_provider
def get_scrobbles_of_artist(artist,since=None,to=None,resolve_references=True,dbconn=None):

	if since is None: since=0
	if to is None: to=now()

	artist_id = get_artist_id(artist,dbconn=dbconn)

	jointable = sql.join(DB['scrobbles'],DB['trackartists'],DB['scrobbles'].c.track_id == DB['trackartists'].c.track_id)

	op = jointable.select().where(
		DB['scrobbles'].c.timestamp<=to,
		DB['scrobbles'].c.timestamp>=since,
		DB['trackartists'].c.artist_id==artist_id
	).order_by(sql.asc('timestamp'))
	result = dbconn.execute(op).all()

	if resolve_references:
		result = scrobbles_db_to_dict(result,dbconn=dbconn)
	#result = [scrobble_db_to_dict(row,resolve_references=resolve_references) for row in result]
	return result

@cached_wrapper
@connection_provider
def get_scrobbles_of_track(track,since=None,to=None,resolve_references=True,dbconn=None):

	if since is None: since=0
	if to is None: to=now()

	track_id = get_track_id(track,dbconn=dbconn)

	op = DB['scrobbles'].select().where(
		DB['scrobbles'].c.timestamp<=to,
		DB['scrobbles'].c.timestamp>=since,
		DB['scrobbles'].c.track_id==track_id
	).order_by(sql.asc('timestamp'))
	result = dbconn.execute(op).all()

	if resolve_references:
		result = scrobbles_db_to_dict(result)
	#result = [scrobble_db_to_dict(row) for row in result]
	return result

@cached_wrapper
@connection_provider
def get_scrobbles(since=None,to=None,resolve_references=True,dbconn=None):

	if since is None: since=0
	if to is None: to=now()

	op = DB['scrobbles'].select().where(
		DB['scrobbles'].c.timestamp<=to,
		DB['scrobbles'].c.timestamp>=since,
	).order_by(sql.asc('timestamp'))
	result = dbconn.execute(op).all()

	if resolve_references:
		result = scrobbles_db_to_dict(result,dbconn=dbconn)
	#result = [scrobble_db_to_dict(row,resolve_references=resolve_references) for i,row in enumerate(result) if i<max]
	return result


# we can do that with above and resolve_references=False, but just testing speed
@cached_wrapper
@connection_provider
def get_scrobbles_num(since=None,to=None,dbconn=None):

	if since is None: since=0
	if to is None: to=now()

	op = sql.select(sql.func.count()).select_from(DB['scrobbles']).where(
		DB['scrobbles'].c.timestamp<=to,
		DB['scrobbles'].c.timestamp>=since,
	)
	result = dbconn.execute(op).all()

	return result[0][0]

@cached_wrapper
@connection_provider
def get_artists_of_track(track_id,resolve_references=True,dbconn=None):

	op = DB['trackartists'].select().where(
		DB['trackartists'].c.track_id==track_id
	)
	result = dbconn.execute(op).all()

	artists = [get_artist(row.artist_id,dbconn=dbconn) if resolve_references else row.artist_id for row in result]
	return artists


@cached_wrapper
@connection_provider
def get_tracks_of_artist(artist,dbconn=None):

	artist_id = get_artist_id(artist,dbconn=dbconn)

	op = sql.join(DB['tracks'],DB['trackartists']).select().where(
		DB['trackartists'].c.artist_id==artist_id
	)
	result = dbconn.execute(op).all()

	return tracks_db_to_dict(result,dbconn=dbconn)

@cached_wrapper
@connection_provider
def get_artists(dbconn=None):

	op = DB['artists'].select()
	result = dbconn.execute(op).all()

	return artists_db_to_dict(result,dbconn=dbconn)

@cached_wrapper
@connection_provider
def get_tracks(dbconn=None):

	op = DB['tracks'].select()
	result = dbconn.execute(op).all()

	return tracks_db_to_dict(result,dbconn=dbconn)

### functions that count rows for parameters

@cached_wrapper
@connection_provider
def count_scrobbles_by_artist(since,to,resolve_ids=True,dbconn=None):
	jointable = sql.join(
		DB['scrobbles'],
		DB['trackartists'],
		DB['scrobbles'].c.track_id == DB['trackartists'].c.track_id
	)

	jointable2 = sql.join(
		jointable,
		DB['associated_artists'],
		DB['trackartists'].c.artist_id == DB['associated_artists'].c.source_artist,
		isouter=True
	)
	op = sql.select(
		sql.func.count(sql.func.distinct(DB['scrobbles'].c.timestamp)).label('count'),
		# only count distinct scrobbles - because of artist replacement, we could end up
		# with two artists of the same scrobble counting it twice for the same artist
		# e.g. Irene and Seulgi adding two scrobbles to Red Velvet for one real scrobble
		sql.func.coalesce(DB['associated_artists'].c.target_artist,DB['trackartists'].c.artist_id).label('artist_id')
		# use the replaced artist as artist to count if it exists, otherwise original one
	).select_from(jointable2).where(
		DB['scrobbles'].c.timestamp<=to,
		DB['scrobbles'].c.timestamp>=since
	).group_by(
		sql.func.coalesce(DB['associated_artists'].c.target_artist,DB['trackartists'].c.artist_id)
	).order_by(sql.desc('count'))
	result = dbconn.execute(op).all()

	if resolve_ids:
		counts = [row.count for row in result]
		artists = get_artists_map([row.artist_id for row in result],dbconn=dbconn)
		result = [{'scrobbles':row.count,'artist':artists[row.artist_id]} for row in result]
	else:
		result = [{'scrobbles':row.count,'artist_id':row.artist_id} for row in result]
	result = rank(result,key='scrobbles')
	return result

@cached_wrapper
@connection_provider
def count_scrobbles_by_track(since,to,resolve_ids=True,dbconn=None):


	op = sql.select(
		sql.func.count(sql.func.distinct(DB['scrobbles'].c.timestamp)).label('count'),
		DB['scrobbles'].c.track_id
	).select_from(DB['scrobbles']).where(
		DB['scrobbles'].c.timestamp<=to,
		DB['scrobbles'].c.timestamp>=since
	).group_by(DB['scrobbles'].c.track_id).order_by(sql.desc('count'))
	result = dbconn.execute(op).all()

	if resolve_ids:
		counts = [row.count for row in result]
		tracks = get_tracks_map([row.track_id for row in result],dbconn=dbconn)
		result = [{'scrobbles':row.count,'track':tracks[row.track_id]} for row in result]
	else:
		result = [{'scrobbles':row.count,'track_id':row.track_id} for row in result]
	result = rank(result,key='scrobbles')
	return result

@cached_wrapper
@connection_provider
def count_scrobbles_by_track_of_artist(since,to,artist,dbconn=None):

	artist_id = get_artist_id(artist,dbconn=dbconn)

	jointable = sql.join(
		DB['scrobbles'],
		DB['trackartists'],
		DB['scrobbles'].c.track_id == DB['trackartists'].c.track_id
	)

	op = sql.select(
		sql.func.count(sql.func.distinct(DB['scrobbles'].c.timestamp)).label('count'),
		DB['scrobbles'].c.track_id
	).select_from(jointable).filter(
		DB['scrobbles'].c.timestamp<=to,
		DB['scrobbles'].c.timestamp>=since,
		DB['trackartists'].c.artist_id==artist_id
	).group_by(DB['scrobbles'].c.track_id).order_by(sql.desc('count'))
	result = dbconn.execute(op).all()


	counts = [row.count for row in result]
	tracks = get_tracks_map([row.track_id for row in result],dbconn=dbconn)
	result = [{'scrobbles':row.count,'track':tracks[row.track_id]} for row in result]
	result = rank(result,key='scrobbles')
	return result




### functions that get mappings for several entities -> rows

@cached_wrapper_individual
@connection_provider
def get_artists_of_tracks(track_ids,dbconn=None):
	op = sql.join(DB['trackartists'],DB['artists']).select().where(
		DB['trackartists'].c.track_id.in_(track_ids)
	)
	result = dbconn.execute(op).all()

	artists = {}
	for row in result:
		artists.setdefault(row.track_id,[]).append(artist_db_to_dict(row,dbconn=dbconn))
	return artists


@cached_wrapper_individual
@connection_provider
def get_tracks_map(track_ids,dbconn=None):
	op = DB['tracks'].select().where(
		DB['tracks'].c.id.in_(track_ids)
	)
	result = dbconn.execute(op).all()

	tracks = {}
	result = list(result)
	# this will get a list of artistdicts in the correct order of our rows
	trackdicts = tracks_db_to_dict(result,dbconn=dbconn)
	for row,trackdict in zip(result,trackdicts):
		tracks[row.id] = trackdict
	return tracks

@cached_wrapper_individual
@connection_provider
def get_artists_map(artist_ids,dbconn=None):

	op = DB['artists'].select().where(
		DB['artists'].c.id.in_(artist_ids)
	)
	result = dbconn.execute(op).all()

	artists = {}
	result = list(result)
	# this will get a list of artistdicts in the correct order of our rows
	artistdicts = artists_db_to_dict(result,dbconn=dbconn)
	for row,artistdict in zip(result,artistdicts):
		artists[row.id] = artistdict
	return artists


### associations

@cached_wrapper
@connection_provider
def get_associated_artists(*artists,dbconn=None):
	artist_ids = [get_artist_id(a,dbconn=dbconn) for a in artists]

	jointable = sql.join(
		DB['associated_artists'],
		DB['artists'],
		DB['associated_artists'].c.source_artist == DB['artists'].c.id
	)

	op = jointable.select().where(
		DB['associated_artists'].c.target_artist.in_(artist_ids)
	)
	result = dbconn.execute(op).all()

	artists = artists_db_to_dict(result,dbconn=dbconn)
	return artists

@cached_wrapper
@connection_provider
def get_credited_artists(*artists,dbconn=None):
	artist_ids = [get_artist_id(a,dbconn=dbconn) for a in artists]

	jointable = sql.join(
		DB['associated_artists'],
		DB['artists'],
		DB['associated_artists'].c.target_artist == DB['artists'].c.id
	)


	op = jointable.select().where(
		DB['associated_artists'].c.source_artist.in_(artist_ids)
	)
	result = dbconn.execute(op).all()

	artists = artists_db_to_dict(result,dbconn=dbconn)
	return artists


### get a specific entity by id

@cached_wrapper
@connection_provider
def get_track(id,dbconn=None):
	op = DB['tracks'].select().where(
		DB['tracks'].c.id==id
	)
	result = dbconn.execute(op).all()

	trackinfo = result[0]
	return track_db_to_dict(trackinfo,dbconn=dbconn)

@cached_wrapper
@connection_provider
def get_artist(id,dbconn=None):
	op = DB['artists'].select().where(
		DB['artists'].c.id==id
	)
	result = dbconn.execute(op).all()

	artistinfo = result[0]
	return artist_db_to_dict(artistinfo,dbconn=dbconn)


@cached_wrapper
@connection_provider
def get_scrobble(timestamp, include_internal=False, dbconn=None):
	op = DB['scrobbles'].select().where(
		DB['scrobbles'].c.timestamp==timestamp
	)
	result = dbconn.execute(op).all()

	scrobble = result[0]
	return scrobbles_db_to_dict(rows=[scrobble], include_internal=include_internal)[0]

@cached_wrapper
@connection_provider
def search_artist(searchterm,dbconn=None):
	op = DB['artists'].select().where(
		DB['artists'].c.name_normalized.ilike(normalize_name(f"%{searchterm}%"))
	)
	result = dbconn.execute(op).all()

	return [get_artist(row.id,dbconn=dbconn) for row in result]

@cached_wrapper
@connection_provider
def search_track(searchterm,dbconn=None):
	op = DB['tracks'].select().where(
		DB['tracks'].c.title_normalized.ilike(normalize_name(f"%{searchterm}%"))
	)
	result = dbconn.execute(op).all()

	return [get_track(row.id,dbconn=dbconn) for row in result]


##### MAINTENANCE

@runhourly
@connection_provider
def clean_db(dbconn=None):

	log(f"Database Cleanup...")

	to_delete = [
		# tracks with no scrobbles (trackartist entries first)
		"from trackartists where track_id in (select id from tracks where id not in (select track_id from scrobbles))",
		"from tracks where id not in (select track_id from scrobbles)",
		# artists with no tracks
		"from artists where id not in (select artist_id from trackartists) and id not in (select target_artist from associated_artists)",
		# tracks with no artists (scrobbles first)
		"from scrobbles where track_id in (select id from tracks where id not in (select track_id from trackartists))",
		"from tracks where id not in (select track_id from trackartists)"
	]

	for d in to_delete:
		selection = dbconn.execute(sql.text(f"select * {d}"))
		for row in selection.all():
			log(f"Deleting {row}")
		deletion = dbconn.execute(sql.text(f"delete {d}"))

	log("Database Cleanup complete!")



	#if a2+a1>0: log(f"Deleted {a2} tracks without scrobbles ({a1} track artist entries)")

	#if a3>0: log(f"Deleted {a3} artists without tracks")

	#if a5+a4>0: log(f"Deleted {a5} tracks without artists ({a4} scrobbles)")



@runmonthly
def renormalize_names():
	with SCROBBLE_LOCK:
		with engine.begin() as conn:
			rows = conn.execute(DB['artists'].select()).all()

			for row in rows:
				id = row.id
				name = row.name
				norm_actual = row.name_normalized
				norm_target = normalize_name(name)
				if norm_actual != norm_target:
					log(f"{name} should be normalized to {norm_target}, but is instead {norm_actual}, fixing...")

					rows = conn.execute(DB['artists'].update().where(DB['artists'].c.id == id).values(name_normalized=norm_target))


@connection_provider
def merge_duplicate_tracks(artist_id,dbconn=None):
	rows = dbconn.execute(
		DB['trackartists'].select().where(
			DB['trackartists'].c.artist_id == artist_id
		)
	)
	affected_tracks = [r.track_id for r in rows]

	track_artists = {}
	rows = dbconn.execute(
		DB['trackartists'].select().where(
			DB['trackartists'].c.track_id.in_(affected_tracks)
		)
	)


	for row in rows:
		track_artists.setdefault(row.track_id,[]).append(row.artist_id)

	artist_combos = {}
	for track_id in track_artists:
		artist_combos.setdefault(tuple(sorted(track_artists[track_id])),[]).append(track_id)

	for c in artist_combos:
		if len(artist_combos[c]) > 1:
			track_identifiers = {}
			for track_id in artist_combos[c]:
				track_identifiers.setdefault(normalize_name(get_track(track_id)['title']),[]).append(track_id)
			for track in track_identifiers:
				if len(track_identifiers[track]) > 1:
					target,*src = track_identifiers[track]
					merge_tracks(target,src,dbconn=dbconn)











##### AUX FUNCS



# function to turn the name into a representation that can be easily compared, ignoring minor differences
remove_symbols = ["'","`","’"]
replace_with_space = [" - ",": "]
def normalize_name(name):
	for r in replace_with_space:
		name = name.replace(r," ")
	name = "".join(char for char in unicodedata.normalize('NFD',name.lower())
		if char not in remove_symbols and unicodedata.category(char) != 'Mn')
	return name


def now():
	return int(datetime.now().timestamp())

def rank(ls,key):
	for rnk in range(len(ls)):
		if rnk == 0 or ls[rnk][key] < ls[rnk-1][key]:
			ls[rnk]["rank"] = rnk + 1
		else:
			ls[rnk]["rank"] = ls[rnk-1]["rank"]
	return ls
