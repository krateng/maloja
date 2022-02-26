from ..globalconf import data_dir, malojaconfig
from .. import thirdparty
from .. import database

from doreah import caching
from doreah.logging import log

import itertools
import os
import urllib
import random
import base64
import requests
import datauri
import io
from threading import Thread, Timer
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
	sql.Column('expire',sql.Integer)
)
DB['tracks'] = sql.Table(
	'tracks', meta,
	sql.Column('id',sql.Integer,primary_key=True),
	sql.Column('url',sql.String),
	sql.Column('expire',sql.Integer)
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
		return row.url # returns None if nonexistence cached
	return False # no cache entry

def set_image_in_cache(id,table,url):
	remove_image_from_cache(id,table)
	now = int(datetime.datetime.now().timestamp())
	if url is None:
		expire = now + (malojaconfig["CACHE_EXPIRE_NEGATIVE"] * 24 * 3600)
	else:
		expire = now + (malojaconfig["CACHE_EXPIRE_POSITIVE"] * 24 * 3600)
	with engine.begin() as conn:
		op = DB[table].insert().values(
			id=id,
			url=url,
			expire=expire
		)
		result = conn.execute(op)

def remove_image_from_cache(id,table):
	with engine.begin() as conn:
		op = DB[table].delete().where(
			DB[table].c.id==id,
		)
		result = conn.execute(op)

def dl_image(url):
	try:
		r = requests.get(url)
		mime = r.headers.get('content-type','image/jpg')
		data = io.BytesIO(r.content).read()
		uri = datauri.DataURI.make(mime,charset='ascii',base64=True,data=data)
		return uri
	except:
		raise
		return url

def get_track_image(track=None,track_id=None,fast=False):

	if track_id is None:
		track_id = database.sqldb.get_track_id(track)
	title = track['title']
	artists = track['artists']

	# check cache
	result = get_image_from_cache(track_id,'tracks')
	if result is None:
		# nonexistence cached, redirect to artist
		for a in artists:
			return get_artist_image(artist=a,fast=True)
	elif result is False:
		# no cache entry
		pass
	else:
		return result

	# local image
	if malojaconfig["USE_LOCAL_IMAGES"]:
		images = local_files(artists=artists,title=title)
		if len(images) != 0:
			result = random.choice(images)
			result = urllib.parse.quote(result)
			set_image_in_cache(track_id,'tracks',result)
			return result

	# forward
	if fast:
		titlequery = "title=" + urllib.parse.quote(title)
		artistquery = "&".join("artist=" + urllib.parse.quote(a) for a in artists)
		return (f"/image?{titlequery}&{artistquery}")

	# third party
	result = thirdparty.get_image_track_all((artists,title))

	# dl image and proxy
	result = dl_image(result)

	set_image_in_cache(track_id,'tracks',result)
	if result is not None: return result
	for a in artists:
		res = get_artist_image(artist=a,fast=False)
		if res != "": return res
	return ""


def get_artist_image(artist=None,artist_id=None,fast=False):

	if artist_id is None:
		artist_id = database.sqldb.get_artist_id(artist)

	# check cache
	result = get_image_from_cache(artist_id,'artists')
	if result is None:
		# nonexistence cached, whatevs
		return ""
	elif result is False:
		# no cache entry
		pass
	else:
		return result

	# local image
	if malojaconfig["USE_LOCAL_IMAGES"]:
		images = local_files(artist=artist)
		if len(images) != 0:
			result = random.choice(images)
			result = urllib.parse.quote(result)
			set_image_in_cache(artist_id,'artists',result)
			return result

	# forward
	if fast:
		artistquery = "artist=" + urllib.parse.quote(artist)
		return (f"/image?{artistquery}")

	# third party
	result = thirdparty.get_image_artist_all(artist)

	# dl image and proxy
	result = dl_image(result)

	set_image_in_cache(artist_id,'artists',result)
	if result is not None: return result
	return ""


# removes emojis and weird shit from names
def clean(name):
	return "".join(c for c in name if c.isalnum() or c in []).strip()

def get_all_possible_filenames(artist=None,artists=None,title=None):
	# check if we're dealing with a track or artist, then clean up names
	# (only remove non-alphanumeric, allow korean and stuff)

	if title is not None and artists is not None:
		track = True
		title, artists = clean(title), [clean(a) for a in artists]
	elif artist is not None:
		track = False
		artist = clean(artist)
	else: return []


	superfolder = "tracks/" if track else "artists/"

	filenames = []

	if track:
		#unsafeartists = [artist.translate(None,"-_./\\") for artist in artists]
		safeartists = [re.sub("[^a-zA-Z0-9]","",artist) for artist in artists]
		#unsafetitle = title.translate(None,"-_./\\")
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

def local_files(artist=None,artists=None,title=None):


	filenames = get_all_possible_filenames(artist,artists,title)

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
		except:
			pass

	return images



def set_image(b64,**keys):
	track = "title" in keys
	if track:
		entity = {'artists':keys['artists'],'title':keys['title']}
		id = database.sqldb.get_track_id(entity)
	else:
		entity = keys['artist']
		id = database.sqldb.get_artist_id(entity)
	print('id is',id)

	log("Trying to set image, b64 string: " + str(b64[:30] + "..."),module="debug")

	regex = r"data:image/(\w+);base64,(.+)"
	type,b64 = re.fullmatch(regex,b64).groups()
	b64 = base64.b64decode(b64)
	filename = "webupload" + str(int(datetime.datetime.now().timestamp())) + "." + type
	for folder in get_all_possible_filenames(**keys):
		if os.path.exists(data_dir['images'](folder)):
			with open(data_dir['images'](folder,filename),"wb") as f:
				f.write(b64)
			break
	else:
		folder = get_all_possible_filenames(**keys)[0]
		os.makedirs(data_dir['images'](folder))
		with open(data_dir['images'](folder,filename),"wb") as f:
			f.write(b64)

	log("Saved image as " + data_dir['images'](folder,filename),module="debug")

	# set as current picture in rotation
	if track: set_image_in_cache(id,'tracks',os.path.join("/images",folder,filename))
	else: set_image_in_cache(id,'artists',os.path.join("/images",folder,filename))
