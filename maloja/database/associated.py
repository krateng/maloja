## dealing with loading the associated artists rules into a database
## right now this is kind of absurd because we're storing it in a db while not
## actually using its permanence, but this makes it possible to use the information
## directly in sql


import csv
import os

from . import sqldb
from ..pkg_global.conf import data_dir


def load_associated_rules():
	# delete old
	with sqldb.engine.begin() as conn:
		op = sqldb.DB['associated_artists'].delete().where()
		conn.execute(op)

	# load from file
	rawrules = []
	for f in os.listdir(data_dir["rules"]()):
		if f.split('.')[-1].lower() != 'tsv': continue
		filepath = data_dir["rules"](f)
		with open(filepath,'r') as filed:
			reader = csv.reader(filed,delimiter="\t")
			rawrules += [[col for col in entry if col] for entry in reader if len(entry)>0 and not entry[0].startswith('#')]
	rules = [{'source_artist':r[1],'target_artist':r[2]} for r in rawrules if r[0]=="countas"]

	#for rule in rules:
	#	print(f"Rule to replace {rule['source_artist']} with {rule['target_artist']}:")
	#	test = {k:sqldb.get_artist_id(rule[k],create_new=False) for k in rule}
	#	if test['source_artist'] is None: print("axed")

	#allartists = set([*[r['source_artist'] for r in rules],*[r['target_artist'] for r in rules]])

	# find ids
	rules = [{k:sqldb.get_artist_id(rule[k],create_new=False) for k in rule} for rule in rules]
	rules = [r for r in rules if r['source_artist'] is not None]

	# write to db
	ops = [
		sqldb.DB['associated_artists'].insert().values(**r).prefix_with('OR IGNORE')
		for r in rules
	]

	with sqldb.engine.begin() as conn:
		for op in ops:
			conn.execute(op)
