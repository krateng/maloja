import sqlalchemy as sql
import json
import unicodedata
import math
from datetime import datetime

from ..globalconf import data_dir



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

#def scrobble_db_to_dict(row,resolve_references=True):
#	return {
#		"time":row.timestamp,
#		"track":get_track(row.track_id) if resolve_references else row.track_id,
#		"duration":row.duration,
#		"origin":row.origin
#	}


def scrobbles_db_to_dict(rows):
	#track_ids = set(row.track_id for row in rows)
	#tracks = {
	#	track_id:get_track(track_id) for track_id in track_ids
	#}
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

#def track_db_to_dict(row):
#	return {
#		"artists":get_artists_of_track(row.id),
#		"title":row.title,
#		"length":row.length
#	}

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

def artist_db_to_dict(row):
	return row.name

def artists_db_to_dict(rows):
	return [
		row.name
		for row in rows
	]


### DICT -> DB


def scrobble_dict_to_db(info):
	return {
		"rawscrobble":json.dumps(info),
		"timestamp":info['time'],
		"origin":info['origin'],
		"duration":info['duration'],
		"extra":info['extra'],
		"track_id":get_track_id(info['track'])
	}

def track_dict_to_db(info):
	return {
		"title":info['title'],
		"title_normalized":normalize_name(info['title']),
		"length":info['length']
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
			except:
				pass


### these will 'get' the ID of an entity, creating it if necessary


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
			title=trackdict['title'],
			title_normalized=ntitle,
			length=trackdict['length']
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


def get_scrobbles_of_artist(artist,since=None,to=None,resolve_references=True):

	if since is None: since=0
	if to is None: to=now()

	artist_id = get_artist_id(artist)

	jointable = sql.join(DB['scrobbles'],DB['trackartists'],DB['scrobbles'].c.track_id == DB['trackartists'].c.track_id)
	with engine.begin() as conn:
		op = jointable.select().where(
			DB['scrobbles'].c.timestamp<=to,
			DB['scrobbles'].c.timestamp>=since,
			DB['trackartists'].c.artist_id==artist_id
		)
		result = conn.execute(op).all()

	result = scrobbles_db_to_dict(result)
	#result = [scrobble_db_to_dict(row,resolve_references=resolve_references) for row in result]
	return result


def get_scrobbles_of_track(track,since=None,to=None):

	if since is None: since=0
	if to is None: to=now()

	track_id = get_track_id(track)

	with engine.begin() as conn:
		op = DB['scrobbles'].select().where(
			DB['scrobbles'].c.timestamp<=to,
			DB['scrobbles'].c.timestamp>=since,
			DB['scrobbles'].c.track_id==track_id
		)
		result = conn.execute(op).all()

	result = scrobbles_db_to_dict(result)
	#result = [scrobble_db_to_dict(row) for row in result]
	return result


def get_scrobbles(since=None,to=None,resolve_references=True,max=math.inf):

	if since is None: since=0
	if to is None: to=now()

	with engine.begin() as conn:
		op = DB['scrobbles'].select().where(
			DB['scrobbles'].c.timestamp<=to,
			DB['scrobbles'].c.timestamp>=since,
		)
		result = conn.execute(op).all()

	result = scrobbles_db_to_dict(result)
	#result = [scrobble_db_to_dict(row,resolve_references=resolve_references) for i,row in enumerate(result) if i<max]
	return result


def get_artists_of_track(track_id,resolve_references=True):
	with engine.begin() as conn:
		op = DB['trackartists'].select().where(
			DB['trackartists'].c.track_id==track_id
		)
		result = conn.execute(op).all()

	artists = [get_artist(row.artist_id) if resolve_references else row.artist_id for row in result]
	return artists

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

def get_tracks():
	with engine.begin() as conn:
		op = DB['tracks'].select()
		result = conn.execute(op).all()

	return tracks_db_to_dict(result)

def get_tracks_of_artist(artist):

	artist_id = get_artist_id(artist)

	with engine.begin() as conn:
		op = sql.join(DB['tracks'],DB['trackartists']).select().where(
			DB['trackartists'].c.artist_id==artist_id
		)
		result = conn.execute(op).all()

	return tracks_db_to_dict(result)

def get_artists():
	with engine.begin() as conn:
		op = DB['artists'].select()
		result = conn.execute(op).all()

	return artists_db_to_dict(result)


### get a specific entity by id


def get_track(id):
	with engine.begin() as conn:
		op = DB['tracks'].select().where(
			DB['tracks'].c.id==id
		)
		result = conn.execute(op).all()

	trackinfo = result[0]


	result = track_db_to_dict(trackinfo)
	return result


def get_artist(id):
	with engine.begin() as conn:
		op = DB['artists'].select().where(
			DB['artists'].c.id==id
		)
		result = conn.execute(op).all()

	artistinfo = result[0]
	return artist_db_to_dict(artistinfo)




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
