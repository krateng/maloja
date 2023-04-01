from .pkg_global.conf import data_dir, malojaconfig
from . import thirdparty
from . import database

from doreah.logging import log

import itertools
import os
import urllib
import random
import base64
import requests
import datauri
import io
from threading import Thread, Timer, BoundedSemaphore
import re
import datetime

import sqlalchemy as sql




DB = {}
engine = sql.create_engine(f"sqlite:///{data_dir['cache']('images.sqlite')}", echo = False)
meta = sql.MetaData()

DB['artists'] = sql.Table(
	'artists', meta,
	sql.Column('id',sql.Integer,primary_key=True),
	sql.Column('url',sql.String),
	sql.Column('expire',sql.Integer),
	sql.Column('raw',sql.String)
)
DB['tracks'] = sql.Table(
	'tracks', meta,
	sql.Column('id',sql.Integer,primary_key=True),
	sql.Column('url',sql.String),
	sql.Column('expire',sql.Integer),
	sql.Column('raw',sql.String)
)
DB['albums'] = sql.Table(
	'albums', meta,
	sql.Column('id',sql.Integer,primary_key=True),
	sql.Column('url',sql.String),
	sql.Column('expire',sql.Integer),
	sql.Column('raw',sql.String)
)

meta.create_all(engine)

def get_image_from_cache(id,table):
	now = int(datetime.datetime.now().timestamp())
	with engine.begin() as conn:
		op = DB[table].select().where(
			DB[table].c.id==id,
			DB[table].c.expire>now
		)
		result = conn.execute(op).all()
	for row in result:
		if row.raw is not None:
			return {'type':'raw','value':row.raw}
		else:
			return {'type':'url','value':row.url} # returns None as value if nonexistence cached
	return None # no cache entry

def set_image_in_cache(id,table,url):
	remove_image_from_cache(id,table)
	now = int(datetime.datetime.now().timestamp())
	if url is None:
		expire = now + (malojaconfig["CACHE_EXPIRE_NEGATIVE"] * 24 * 3600)
	else:
		expire = now + (malojaconfig["CACHE_EXPIRE_POSITIVE"] * 24 * 3600)

	raw = dl_image(url)

	with engine.begin() as conn:
		op = DB[table].insert().values(
			id=id,
			url=url,
			expire=expire,
			raw=raw
		)
		result = conn.execute(op)

def remove_image_from_cache(id,table):
	with engine.begin() as conn:
		op = DB[table].delete().where(
			DB[table].c.id==id,
		)
		result = conn.execute(op)

def dl_image(url):
	if not malojaconfig["PROXY_IMAGES"]: return None
	if url is None: return None
	if url.startswith("/"): return None #local image
	try:
		r = requests.get(url)
		mime = r.headers.get('content-type') or 'image/jpg'
		data = io.BytesIO(r.content).read()
		uri = datauri.DataURI.make(mime,charset='ascii',base64=True,data=data)
		log(f"Downloaded {url} for local caching")
		return uri
	except Exception:
		log(f"Image {url} could not be downloaded for local caching")
		return None



### getting images for any website embedding now ALWAYS returns just the generic link
### even if we have already cached it, we will handle that on request
def get_track_image(track=None,track_id=None):
	if track_id is None:
		track_id = database.sqldb.get_track_id(track,create_new=False)

	return f"/image?type=track&id={track_id}"


def get_artist_image(artist=None,artist_id=None):
	if artist_id is None:
		artist_id = database.sqldb.get_artist_id(artist,create_new=False)

	return f"/image?type=artist&id={artist_id}"

def get_album_image(album=None,album_id=None):
	if album_id is None:
		album_id = database.sqldb.get_album_id(album,create_new=False)

	return f"/image?type=album&id={album_id}"


resolve_semaphore = BoundedSemaphore(8)


def resolve_track_image(track_id):

	if malojaconfig["USE_ALBUM_ARTWORK_FOR_TRACKS"]:
		track = database.sqldb.get_track(track_id)
		if "album" in track:
			album_id = database.sqldb.get_album_id(track["album"])
			albumart = resolve_album_image(album_id)
			if albumart:
				return albumart

	with resolve_semaphore:
		# check cache
		result = get_image_from_cache(track_id,'tracks')
		if result is not None:
			return result

		track = database.sqldb.get_track(track_id)

		# local image
		if malojaconfig["USE_LOCAL_IMAGES"]:
			images = local_files(track=track)
			if len(images) != 0:
				result = random.choice(images)
				result = urllib.parse.quote(result)
				result = {'type':'url','value':result}
				set_image_in_cache(track_id,'tracks',result['value'])
				return result

		# third party
		result = thirdparty.get_image_track_all((track['artists'],track['title']))
		result = {'type':'url','value':result}
		set_image_in_cache(track_id,'tracks',result['value'])

		return result


def resolve_artist_image(artist_id):

	with resolve_semaphore:
		# check cache
		result = get_image_from_cache(artist_id,'artists')
		if result is not None:
			return result

		artist = database.sqldb.get_artist(artist_id)

		# local image
		if malojaconfig["USE_LOCAL_IMAGES"]:
			images = local_files(artist=artist)
			if len(images) != 0:
				result = random.choice(images)
				result = urllib.parse.quote(result)
				result = {'type':'url','value':result}
				set_image_in_cache(artist_id,'artists',result['value'])
				return result

		# third party
		result = thirdparty.get_image_artist_all(artist)
		result = {'type':'url','value':result}
		set_image_in_cache(artist_id,'artists',result['value'])

		return result


def resolve_album_image(album_id):

	with resolve_semaphore:
		# check cache
		result = get_image_from_cache(album_id,'albums')
		if result is not None:
			return result

		album = database.sqldb.get_album(album_id)

		# local image
		if malojaconfig["USE_LOCAL_IMAGES"]:
			images = local_files(album=album)
			if len(images) != 0:
				result = random.choice(images)
				result = urllib.parse.quote(result)
				result = {'type':'url','value':result}
				set_image_in_cache(album_id,'tracks',result['value'])
				return result

		# third party
		result = thirdparty.get_image_album_all((album['artists'],album['albumtitle']))
		result = {'type':'url','value':result}
		set_image_in_cache(album_id,'albums',result['value'])

		return result


# removes emojis and weird shit from names
def clean(name):
	return "".join(c for c in name if c.isalnum() or c in []).strip()

# new and improved
def get_all_possible_filenames(artist=None,track=None,album=None):
	if track:
		title, artists = clean(track['title']), [clean(a) for a in track['artists']]
		superfolder = "tracks/"
	elif album:
		title, artists = clean(album['albumtitle']), [clean(a) for a in album.get('artists') or []]
		superfolder = "albums/"
	elif artist:
		artist = clean(artist)
		superfolder = "artists/"
	else:
		return []

	filenames = []

	if track or album:
		safeartists = [re.sub("[^a-zA-Z0-9]","",artist) for artist in artists]
		safetitle = re.sub("[^a-zA-Z0-9]","",title)

		if len(artists) < 4:
			unsafeperms = itertools.permutations(artists)
			safeperms = itertools.permutations(safeartists)
		else:
			unsafeperms = [sorted(artists)]
			safeperms = [sorted(safeartists)]

		for unsafeartistlist in unsafeperms:
			filename = "-".join(unsafeartistlist) + "_" + title
			if filename != "":
				filenames.append(filename)
				filenames.append(filename.lower())
		for safeartistlist in safeperms:
			filename = "-".join(safeartistlist) + "_" + safetitle
			if filename != "":
				filenames.append(filename)
				filenames.append(filename.lower())
		filenames = list(set(filenames))
		if len(filenames) == 0: filenames.append(str(hash((frozenset(artists),title))))
	else:
		#unsafeartist = artist.translate(None,"-_./\\")
		safeartist = re.sub("[^a-zA-Z0-9]","",artist)

		filename = artist
		if filename != "":
			filenames.append(filename)
			filenames.append(filename.lower())
		filename = safeartist
		if filename != "":
			filenames.append(filename)
			filenames.append(filename.lower())

		filenames = list(set(filenames))
		if len(filenames) == 0: filenames.append(str(hash(artist)))

	return [superfolder + name for name in filenames]


def local_files(artist=None,album=None,track=None):


	filenames = get_all_possible_filenames(artist=artist,album=album,track=track)

	images = []

	for purename in filenames:
		# direct files
		for ext in ["png","jpg","jpeg","gif"]:
			#for num in [""] + [str(n) for n in range(0,10)]:
			if os.path.exists(data_dir['images'](purename + "." + ext)):
				images.append("/images/" + purename + "." + ext)

		# folder
		try:
			for f in os.listdir(data_dir['images'](purename)):
				if f.split(".")[-1] in ["png","jpg","jpeg","gif"]:
					images.append("/images/" + purename + "/" + f)
		except Exception:
			pass

	return images



class MalformedB64(Exception):
	pass

def set_image(b64,**keys):
	if "title" in keys:
		entity = {"track":keys}
		id = database.sqldb.get_track_id(entity['track'])
		dbtable = "tracks"
	elif "albumtitle" in keys:
		entity = {"album":keys}
		id = database.sqldb.get_album_id(entity['album'])
		dbtable = "albums"
	elif "artist" in keys:
		entity = keys
		id = database.sqldb.get_artist_id(entity['artist'])
		dbtable = "artists"

	log("Trying to set image, b64 string: " + str(b64[:30] + "..."),module="debug")

	regex = r"data:image/(\w+);base64,(.+)"
	match = re.fullmatch(regex,b64)
	if not match: raise MalformedB64()

	type,b64 = match.groups()
	b64 = base64.b64decode(b64)
	filename = "webupload" + str(int(datetime.datetime.now().timestamp())) + "." + type
	for folder in get_all_possible_filenames(**entity):
		if os.path.exists(data_dir['images'](folder)):
			with open(data_dir['images'](folder,filename),"wb") as f:
				f.write(b64)
			break
	else:
		folder = get_all_possible_filenames(**entity)[0]
		os.makedirs(data_dir['images'](folder))
		with open(data_dir['images'](folder,filename),"wb") as f:
			f.write(b64)


	log("Saved image as " + data_dir['images'](folder,filename),module="debug")

	# set as current picture in rotation
	set_image_in_cache(id,dbtable,os.path.join("/images",folder,filename))

	return os.path.join("/images",folder,filename)
