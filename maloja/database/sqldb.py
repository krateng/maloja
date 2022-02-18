import sqlalchemy as sql
import json
import unicodedata
import math
from datetime import datetime

from ..globalconf import data_dir

from .dbcache import cached_wrapper

from doreah.logging import log
from doreah.regular import runhourly



##### DB Technical

DB = {}


engine = sql.create_engine(f"sqlite:///{data_dir['scrobbles']('malojadb.sqlite')}", echo = False)
meta = sql.MetaData()

DB['scrobbles'] = sql.Table(
	'scrobbles', meta,
	sql.Column('timestamp',sql.Integer,primary_key=True),
	sql.Column('rawscrobble',sql.String),
	sql.Column('origin',sql.String),
	sql.Column('duration',sql.Integer),
	sql.Column('track_id',sql.Integer,sql.ForeignKey('tracks.id'))
)
DB['tracks'] = sql.Table(
	'tracks', meta,
	sql.Column('id',sql.Integer,primary_key=True),
	sql.Column('title',sql.String),
	sql.Column('title_normalized',sql.String),
	sql.Column('length',sql.Integer)
)
DB['artists'] = sql.Table(
	'artists', meta,
	sql.Column('id',sql.Integer,primary_key=True),
	sql.Column('name',sql.String),
	sql.Column('name_normalized',sql.String)
)
DB['trackartists'] = sql.Table(
	'trackartists', meta,
	sql.Column('id',sql.Integer,primary_key=True),
	sql.Column('artist_id',sql.Integer,sql.ForeignKey('artists.id')),
	sql.Column('track_id',sql.Integer,sql.ForeignKey('tracks.id'))
)

DB['associated_artists'] = sql.Table(
	'associated_artists', meta,
	sql.Column('source_artist',sql.Integer,sql.ForeignKey('artists.id')),
	sql.Column('target_artist',sql.Integer,sql.ForeignKey('artists.id')),
	sql.UniqueConstraint('source_artist', 'target_artist')
)

meta.create_all(engine)

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
#	"extra":{string-keyed mapping for all flags with the scrobble}
# }




##### Conversions between DB and dicts

# These should work on whole lists and collect all the references,
# then look them up once and fill them in


### DB -> DICT
def scrobbles_db_to_dict(rows):
	tracks = get_tracks_map(set(row.track_id for row in rows))
	return [
		{
			"time":row.timestamp,
			"track":tracks[row.track_id],
			"duration":row.duration,
			"origin":row.origin
		}
		for row in rows
	]

def scrobble_db_to_dict(row):
	return scrobbles_db_to_dict([row])[0]

def tracks_db_to_dict(rows):
	artists = get_artists_of_tracks(set(row.id for row in rows))
	return [
		{
			"artists":artists[row.id],
			"title":row.title,
			"length":row.length
		}
		for row in rows
	]

def track_db_to_dict(row):
	return tracks_db_to_dict([row])[0]

def artists_db_to_dict(rows):
	return [
		row.name
		for row in rows
	]

def artist_db_to_dict(row):
	return artists_db_to_dict([row])[0]




### DICT -> DB
# TODO

def scrobble_dict_to_db(info):
	return {
		"rawscrobble":json.dumps(info),
		"timestamp":info['time'],
		"origin":info['origin'],
		"duration":info['duration'],
		"track_id":get_track_id(info['track'])
	}

def track_dict_to_db(info):
	return {
		"title":info['title'],
		"title_normalized":normalize_name(info['title']),
		"length":info.get('length')
	}

def artist_dict_to_db(info):
	return {
		"name": info,
		"name_normalized":normalize_name(info)
	}





##### Actual Database interactions


def add_scrobble(scrobbledict):
	add_scrobbles([scrobbledict])

def add_scrobbles(scrobbleslist):

	ops = [
		DB['scrobbles'].insert().values(
			**scrobble_dict_to_db(s)
		) for s in scrobbleslist
	]

	with engine.begin() as conn:
		for op in ops:
			try:
				conn.execute(op)
			except sql.exc.IntegrityError:
				pass


### these will 'get' the ID of an entity, creating it if necessary

@cached_wrapper
def get_track_id(trackdict):
	ntitle = normalize_name(trackdict['title'])
	artist_ids = [get_artist_id(a) for a in trackdict['artists']]



	with engine.begin() as conn:
		op = DB['tracks'].select(
			DB['tracks'].c.id
		).where(
			DB['tracks'].c.title_normalized==ntitle
		)
		result = conn.execute(op).all()
	for row in result:
		# check if the artists are the same
		foundtrackartists = []
		with engine.begin() as conn:
			op = DB['trackartists'].select(
				DB['trackartists'].c.artist_id
			).where(
				DB['trackartists'].c.track_id==row[0]
			)
			result = conn.execute(op).all()
		match_artist_ids = [r.artist_id for r in result]
		#print("required artists",artist_ids,"this match",match_artist_ids)
		if set(artist_ids) == set(match_artist_ids):
			#print("ID for",trackdict['title'],"was",row[0])
			return row.id

	with engine.begin() as conn:
		op = DB['tracks'].insert().values(
			**track_dict_to_db(trackdict)
		)
		result = conn.execute(op)
		track_id = result.inserted_primary_key[0]
	with engine.begin() as conn:
		for artist_id in artist_ids:
			op = DB['trackartists'].insert().values(
				track_id=track_id,
				artist_id=artist_id
			)
			result = conn.execute(op)
		#print("Created",trackdict['title'],track_id)
		return track_id

@cached_wrapper
def get_artist_id(artistname):
	nname = normalize_name(artistname)
	#print("looking for",nname)

	with engine.begin() as conn:
		op = DB['artists'].select(
			DB['artists'].c.id
		).where(
			DB['artists'].c.name_normalized==nname
		)
		result = conn.execute(op).all()
	for row in result:
		#print("ID for",artistname,"was",row[0])
		return row.id

	with engine.begin() as conn:
		op = DB['artists'].insert().values(
			name=artistname,
			name_normalized=nname
		)
		result = conn.execute(op)
		#print("Created",artistname,result.inserted_primary_key)
		return result.inserted_primary_key[0]





### Functions that get rows according to parameters

@cached_wrapper
def get_scrobbles_of_artist(artist,since=None,to=None):

	if since is None: since=0
	if to is None: to=now()

	artist_id = get_artist_id(artist)

	jointable = sql.join(DB['scrobbles'],DB['trackartists'],DB['scrobbles'].c.track_id == DB['trackartists'].c.track_id)
	with engine.begin() as conn:
		op = jointable.select().where(
			DB['scrobbles'].c.timestamp<=to,
			DB['scrobbles'].c.timestamp>=since,
			DB['trackartists'].c.artist_id==artist_id
		).order_by(sql.asc('timestamp'))
		result = conn.execute(op).all()

	result = scrobbles_db_to_dict(result)
	#result = [scrobble_db_to_dict(row,resolve_references=resolve_references) for row in result]
	return result

@cached_wrapper
def get_scrobbles_of_track(track,since=None,to=None):

	if since is None: since=0
	if to is None: to=now()

	track_id = get_track_id(track)

	with engine.begin() as conn:
		op = DB['scrobbles'].select().where(
			DB['scrobbles'].c.timestamp<=to,
			DB['scrobbles'].c.timestamp>=since,
			DB['scrobbles'].c.track_id==track_id
		).order_by(sql.asc('timestamp'))
		result = conn.execute(op).all()

	result = scrobbles_db_to_dict(result)
	#result = [scrobble_db_to_dict(row) for row in result]
	return result

@cached_wrapper
def get_scrobbles(since=None,to=None,resolve_references=True):

	if since is None: since=0
	if to is None: to=now()

	with engine.begin() as conn:
		op = DB['scrobbles'].select().where(
			DB['scrobbles'].c.timestamp<=to,
			DB['scrobbles'].c.timestamp>=since,
		).order_by(sql.asc('timestamp'))
		result = conn.execute(op).all()

	result = scrobbles_db_to_dict(result)
	#result = [scrobble_db_to_dict(row,resolve_references=resolve_references) for i,row in enumerate(result) if i<max]
	return result

@cached_wrapper
def get_artists_of_track(track_id,resolve_references=True):
	with engine.begin() as conn:
		op = DB['trackartists'].select().where(
			DB['trackartists'].c.track_id==track_id
		)
		result = conn.execute(op).all()

	artists = [get_artist(row.artist_id) if resolve_references else row.artist_id for row in result]
	return artists


@cached_wrapper
def get_tracks_of_artist(artist):

	artist_id = get_artist_id(artist)

	with engine.begin() as conn:
		op = sql.join(DB['tracks'],DB['trackartists']).select().where(
			DB['trackartists'].c.artist_id==artist_id
		)
		result = conn.execute(op).all()

	return tracks_db_to_dict(result)

@cached_wrapper
def get_artists():
	with engine.begin() as conn:
		op = DB['artists'].select()
		result = conn.execute(op).all()

	return artists_db_to_dict(result)

@cached_wrapper
def get_tracks():
	with engine.begin() as conn:
		op = DB['tracks'].select()
		result = conn.execute(op).all()

	return tracks_db_to_dict(result)

### functions that count rows for parameters

@cached_wrapper
def count_scrobbles_by_artist(since,to):
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
	with engine.begin() as conn:
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
		result = conn.execute(op).all()


	counts = [row.count for row in result]
	artists = get_artists_map([row.artist_id for row in result])
	result = [{'scrobbles':row.count,'artist':artists[row.artist_id]} for row in result]
	result = rank(result,key='scrobbles')
	return result

@cached_wrapper
def count_scrobbles_by_track(since,to):

	with engine.begin() as conn:
		op = sql.select(
			sql.func.count(sql.func.distinct(DB['scrobbles'].c.timestamp)).label('count'),
			DB['scrobbles'].c.track_id
		).select_from(DB['scrobbles']).where(
			DB['scrobbles'].c.timestamp<=to,
			DB['scrobbles'].c.timestamp>=since
		).group_by(DB['scrobbles'].c.track_id).order_by(sql.desc('count'))
		result = conn.execute(op).all()


	counts = [row.count for row in result]
	tracks = get_tracks_map([row.track_id for row in result])
	result = [{'scrobbles':row.count,'track':tracks[row.track_id]} for row in result]
	result = rank(result,key='scrobbles')
	return result

@cached_wrapper
def count_scrobbles_by_track_of_artist(since,to,artist):

	artist_id = get_artist_id(artist)

	jointable = sql.join(
		DB['scrobbles'],
		DB['trackartists'],
		DB['scrobbles'].c.track_id == DB['trackartists'].c.track_id
	)

	with engine.begin() as conn:
		op = sql.select(
			sql.func.count(sql.func.distinct(DB['scrobbles'].c.timestamp)).label('count'),
			DB['scrobbles'].c.track_id
		).select_from(jointable).filter(
			DB['scrobbles'].c.timestamp<=to,
			DB['scrobbles'].c.timestamp>=since,
			DB['trackartists'].c.artist_id==artist_id
		).group_by(DB['scrobbles'].c.track_id).order_by(sql.desc('count'))
		result = conn.execute(op).all()


	counts = [row.count for row in result]
	tracks = get_tracks_map([row.track_id for row in result])
	result = [{'scrobbles':row.count,'track':tracks[row.track_id]} for row in result]
	result = rank(result,key='scrobbles')
	return result




### functions that get mappings for several entities -> rows

@cached_wrapper
def get_artists_of_tracks(track_ids):
	with engine.begin() as conn:
		op = sql.join(DB['trackartists'],DB['artists']).select().where(
			DB['trackartists'].c.track_id.in_(track_ids)
		)
		result = conn.execute(op).all()

	artists = {}
	for row in result:
		artists.setdefault(row.track_id,[]).append(artist_db_to_dict(row))
	return artists


@cached_wrapper
def get_tracks_map(track_ids):
	with engine.begin() as conn:
		op = DB['tracks'].select().where(
			DB['tracks'].c.id.in_(track_ids)
		)
		result = conn.execute(op).all()

	tracks = {}
	trackids = [row.id for row in result]
	trackdicts = tracks_db_to_dict(result)
	for i in range(len(trackids)):
		tracks[trackids[i]] = trackdicts[i]
	return tracks

@cached_wrapper
def get_artists_map(artist_ids):
	with engine.begin() as conn:
		op = DB['artists'].select().where(
			DB['artists'].c.id.in_(artist_ids)
		)
		result = conn.execute(op).all()

	artists = {}
	artistids = [row.id for row in result]
	artistdicts = artists_db_to_dict(result)
	for i in range(len(artistids)):
		artists[artistids[i]] = artistdicts[i]
	return artists


### associations

@cached_wrapper
def get_associated_artists(*artists):
	artist_ids = [get_artist_id(a) for a in artists]

	jointable = sql.join(
		DB['associated_artists'],
		DB['artists'],
		DB['associated_artists'].c.source_artist == DB['artists'].c.id
	)

	with engine.begin() as conn:
		op = jointable.select().where(
			DB['associated_artists'].c.target_artist.in_(artist_ids)
		)
		result = conn.execute(op).all()

	artists = artists_db_to_dict(result)
	return artists

@cached_wrapper
def get_credited_artists(*artists):
	artist_ids = [get_artist_id(a) for a in artists]

	jointable = sql.join(
		DB['associated_artists'],
		DB['artists'],
		DB['associated_artists'].c.target_artist == DB['artists'].c.id
	)

	with engine.begin() as conn:
		op = jointable.select().where(
			DB['associated_artists'].c.source_artist.in_(artist_ids)
		)
		result = conn.execute(op).all()

	artists = artists_db_to_dict(result)
	return artists


### get a specific entity by id

@cached_wrapper
def get_track(id):
	with engine.begin() as conn:
		op = DB['tracks'].select().where(
			DB['tracks'].c.id==id
		)
		result = conn.execute(op).all()

	trackinfo = result[0]
	return track_db_to_dict(trackinfo)

@cached_wrapper
def get_artist(id):
	with engine.begin() as conn:
		op = DB['artists'].select().where(
			DB['artists'].c.id==id
		)
		result = conn.execute(op).all()

	artistinfo = result[0]
	return artist_db_to_dict(artistinfo)





##### MAINTENANCE

@runhourly
def clean_db():
	with engine.begin() as conn:
		log(f"Database Cleanup...")

		### Delete tracks that have no scrobbles (delete their trackartist entries first)
		a1 = conn.execute(sql.text('''
			delete from trackartists where track_id in (select id from tracks where id not in (select track_id from scrobbles))
		''')).rowcount
		a2 = conn.execute(sql.text('''
			delete from tracks where id not in (select track_id from scrobbles)
		''')).rowcount

		log(f"Deleted {a2} tracks without scrobbles ({a1} track artist entries)")

		### Delete artists that have no tracks
		# we actually don't wanna do that as it will break collection artists
		# that don't have songs themselves
		#a3 = conn.execute(sql.text('''
		#	delete from artists where id not in (select artist_id from trackartists)
		#''')).rowcount
		#
		#log(f"Deleted {a3} artists without tracks")

		### Delete tracks that have no artists (delete their scrobbles first)
		a4 = conn.execute(sql.text('''
			delete from scrobbles where track_id in (select id from tracks where id not in (select track_id from trackartists))
		''')).rowcount
		a5 = conn.execute(sql.text('''
			delete from tracks where id not in (select track_id from trackartists)
		''')).rowcount

		log(f"Deleted {a5} tracks without artists ({a4} scrobbles)")












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
