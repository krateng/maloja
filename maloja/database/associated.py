## dealing with loading the associated artists rules into a database
## right now this is kind of absurd because we're storing it in a db while not
## actually using its permanence, but this makes it possible to use the information
## directly in sql


from doreah import tsv


from . import sqldb
from ..globalconf import data_dir


def load_associated_rules():
	# delete old
	with sqldb.engine.begin() as conn:
		op = sqldb.DB['associated_artists'].delete().where()
		conn.execute(op)

	# load from file
	raw = tsv.parse_all(data_dir["rules"](),"string","string","string")
	rules = [{'source_artist':b,'target_artist':c} for [a,b,c] in raw if a=="countas"]
	#allartists = set([*[r['source_artist'] for r in rules],*[r['target_artist'] for r in rules]])

	# find ids
	rules = [{k:sqldb.get_artist_id(rule[k]) for k in rule} for rule in rules]

	# write to db
	ops = [
		sqldb.DB['associated_artists'].insert().values(**r)
		for r in rules
	]

	with sqldb.engine.begin() as conn:
		for op in ops:
			conn.execute(op)
