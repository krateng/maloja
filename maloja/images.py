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
from threading import Lock
from concurrent.futures import ThreadPoolExecutor
import re
import datetime
import time

import sqlalchemy as sql



MAX_RESOLVE_THREADS = 5
MAX_SECONDS_TO_RESOLVE_REQUEST = 5


# remove old db file (columns missing)
try:
	os.remove(data_dir['cache']('images.sqlite'))
except:
	pass

DB = {}
engine = sql.create_engine(f"sqlite:///{data_dir['cache']('imagecache.sqlite')}", echo = False)
meta = sql.MetaData()

dblock = Lock()

DB['artists'] = sql.Table(
	'artists', meta,
	sql.Column('id',sql.Integer,primary_key=True),
	sql.Column('url',sql.String),
	sql.Column('expire',sql.Integer),
#	sql.Column('raw',sql.String)
	sql.Column('local',sql.Boolean),
	sql.Column('localproxyurl',sql.String)
)
DB['tracks'] = sql.Table(
	'tracks', meta,
	sql.Column('id',sql.Integer,primary_key=True),
	sql.Column('url',sql.String),
	sql.Column('expire',sql.Integer),
#	sql.Column('raw',sql.String)
	sql.Column('local',sql.Boolean),
	sql.Column('localproxyurl',sql.String)
)
DB['albums'] = sql.Table(
	'albums', meta,
	sql.Column('id',sql.Integer,primary_key=True),
	sql.Column('url',sql.String),
	sql.Column('expire',sql.Integer),
#	sql.Column('raw',sql.String)
	sql.Column('local',sql.Boolean),
	sql.Column('localproxyurl',sql.String)
)

meta.create_all(engine)

def get_id_and_table(track_id=None,artist_id=None,album_id=None):
	if track_id:
		return track_id,'tracks'
	elif album_id:
		return album_id,'albums'
	elif artist_id:
		return artist_id,'artists'

def get_image_from_cache(track_id=None,artist_id=None,album_id=None):
	now = int(datetime.datetime.now().timestamp())
	entity_id, table = get_id_and_table(track_id=track_id,artist_id=artist_id,album_id=album_id)

	with engine.begin() as conn:
		op = DB[table].select().where(
			DB[table].c.id==entity_id,
			DB[table].c.expire>now
		)
		result = conn.execute(op).all()
	for row in result:
		if row.local:
			return {'type':'localurl','value':row.url}
		elif row.localproxyurl:
			return {'type':'localurl','value':row.localproxyurl}
		else:
			return {'type':'url','value':row.url or None}
			# value none means nonexistence is cached
			# for some reason this can also be an empty string, so use or None here to unify
	return None # no cache entry

def set_image_in_cache(url,track_id=None,artist_id=None,album_id=None,local=False):
	remove_image_from_cache(track_id=track_id,artist_id=artist_id,album_id=album_id)
	entity_id, table = get_id_and_table(track_id=track_id,artist_id=artist_id,album_id=album_id)

	with dblock:
		now = int(datetime.datetime.now().timestamp())
		if url is None:
			expire = now + (malojaconfig["CACHE_EXPIRE_NEGATIVE"] * 24 * 3600)
		else:
			expire = now + (malojaconfig["CACHE_EXPIRE_POSITIVE"] * 24 * 3600)

		if not local and malojaconfig["PROXY_IMAGES"] and url is not None:
			localproxyurl = dl_image(url)
		else:
			localproxyurl = None

		with engine.begin() as conn:
			op = DB[table].insert().values(
				id=entity_id,
				url=url,
				expire=expire,
				local=local,
				localproxyurl=localproxyurl
			)
			result = conn.execute(op)

def remove_image_from_cache(track_id=None,artist_id=None,album_id=None):
	entity_id, table = get_id_and_table(track_id=track_id,artist_id=artist_id,album_id=album_id)

	with dblock:
		with engine.begin() as conn:
			op = DB[table].delete().where(
				DB[table].c.id==entity_id,
			).returning(
				DB[table].c.id,
				DB[table].c.localproxyurl
			)
			result = conn.execute(op).all()

		for row in result:
			try:
				targetpath = data_dir['cache']('images',row.localproxyurl.split('/')[-1])
				os.remove(targetpath)
			except:
				pass


def dl_image(url):
	try:
		r = requests.get(url)
		mime = r.headers.get('content-type') or 'image/jpg'
		data = io.BytesIO(r.content).read()
		#uri = datauri.DataURI.make(mime,charset='ascii',base64=True,data=data)
		targetname = '%030x' % random.getrandbits(128)
		targetpath = data_dir['cache']('images',targetname)
		with open(targetpath,'wb') as fd:
			fd.write(data)
		return os.path.join("/cacheimages",targetname)
	except Exception:
		log(f"Image {url} could not be downloaded for local caching")
		return None




resolver = ThreadPoolExecutor(max_workers=MAX_RESOLVE_THREADS,thread_name_prefix='image_resolve')

### getting images for any website embedding now ALWAYS returns just the generic link
### even if we have already cached it, we will handle that on request
def get_track_image(track=None,track_id=None):
	if track_id is None:
		track_id = database.sqldb.get_track_id(track,create_new=False)

	if malojaconfig["USE_ALBUM_ARTWORK_FOR_TRACKS"]:
		if track is None:
			track = database.sqldb.get_track(track_id)
		if track.get("album"):
			album_id = database.sqldb.get_album_id(track["album"])
			return get_album_image(album_id=album_id)

	resolver.submit(resolve_image,track_id=track_id)

	return f"/image?track_id={track_id}"

def get_artist_image(artist=None,artist_id=None):
	if artist_id is None:
		artist_id = database.sqldb.get_artist_id(artist,create_new=False)

	resolver.submit(resolve_image,artist_id=artist_id)

	return f"/image?artist_id={artist_id}"

def get_album_image(album=None,album_id=None):
	if album_id is None:
		album_id = database.sqldb.get_album_id(album,create_new=False)

	resolver.submit(resolve_image,album_id=album_id)

	return f"/image?album_id={album_id}"


# this is to keep track of what is currently being resolved
# so new requests know that they don't need to queue another resolve
image_resolve_controller_lock = Lock()
image_resolve_controller = {
	'artists':set(),
	'albums':set(),
	'tracks':set()
}

# this function doesn't need to return any info
# it runs async to do all the work that takes time and only needs to write the result
# to the cache so the synchronous functions (http requests) can access it
def resolve_image(artist_id=None,track_id=None,album_id=None):
	result = get_image_from_cache(artist_id=artist_id,track_id=track_id,album_id=album_id)
	if result is not None:
		# No need to do anything
		return

	if artist_id:
		entitytype = 'artist'
		table = 'artists'
		getfunc, entity_id = database.sqldb.get_artist, artist_id
	elif track_id:
		entitytype = 'track'
		table = 'tracks'
		getfunc, entity_id = database.sqldb.get_track, track_id
	elif album_id:
		entitytype = 'album'
		table = 'albums'
		getfunc, entity_id = database.sqldb.get_album, album_id



	# is another thread already working on this?
	with image_resolve_controller_lock:
		if entity_id in image_resolve_controller[table]:
			return
		else:
			image_resolve_controller[table].add(entity_id)




	try:
		entity = getfunc(entity_id)

		# local image
		if malojaconfig["USE_LOCAL_IMAGES"]:
			images = local_files(**{entitytype: entity})
			if len(images) != 0:
				result = random.choice(images)
				result = urllib.parse.quote(result)
				result = {'type':'localurl','value':result}
				set_image_in_cache(artist_id=artist_id,track_id=track_id,album_id=album_id,url=result['value'],local=True)
				return result

		# third party
		if artist_id:
			result = thirdparty.get_image_artist_all(entity)
		elif track_id:
			result = thirdparty.get_image_track_all((entity['artists'],entity['title']))
		elif album_id:
			result = thirdparty.get_image_album_all((entity['artists'],entity['albumtitle']))

		result = {'type':'url','value':result or None}
		set_image_in_cache(artist_id=artist_id,track_id=track_id,album_id=album_id,url=result['value'])
	finally:
		with image_resolve_controller_lock:
			image_resolve_controller[table].remove(entity_id)



# the actual http request for the full image
def image_request(artist_id=None,track_id=None,album_id=None):

	# because we use lazyload, we can allow our http requests to take a little while at least
	# not the full backend request, but a few seconds to give us time to fetch some images
	# because 503 retry-after doesn't seem to be honored
	attempt = 0
	while attempt < MAX_SECONDS_TO_RESOLVE_REQUEST:
		attempt += 1
		# check cache
		result = get_image_from_cache(artist_id=artist_id,track_id=track_id,album_id=album_id)
		if result is not None:
			# we got an entry, even if it's that there is no image (value None)
			if result['value'] is None:
				# use placeholder
				if malojaconfig["FANCY_PLACEHOLDER_ART"]:
					placeholder_url = "https://generative-placeholders.glitch.me/image?width=300&height=300&style="
					if artist_id:
						result['value'] = placeholder_url + f"tiles&colors={artist_id % 100}"
					if track_id:
						result['value'] = placeholder_url + f"triangles&colors={track_id % 100}"
					if album_id:
						result['value'] = placeholder_url + f"joy-division&colors={album_id % 100}"
				else:
					if artist_id:
						result['value'] = "/static/svg/placeholder_artist.svg"
					if track_id:
						result['value'] = "/static/svg/placeholder_track.svg"
					if album_id:
						result['value'] = "/static/svg/placeholder_album.svg"
			return result
		time.sleep(1)

	# no entry, which means we're still working on it
	return {'type':'noimage','value':'wait'}



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
		idkeys = {'track_id':id}
		dbtable = "tracks"
	elif "albumtitle" in keys:
		entity = {"album":keys}
		id = database.sqldb.get_album_id(entity['album'])
		idkeys = {'album_id':id}
		dbtable = "albums"
	elif "artist" in keys:
		entity = keys
		id = database.sqldb.get_artist_id(entity['artist'])
		idkeys = {'artist_id':id}
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
	set_image_in_cache(**idkeys,url=os.path.join("/images",folder,filename),local=True)

	return os.path.join("/images",folder,filename)
