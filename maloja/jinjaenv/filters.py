def fixlength(real,target):
	t = real[:target]
	while len(t)<target: t.append(None)
	return t

def find_representative(sequence,attribute_id,attribute_count):
	try:
		newsequence = [e for e in sequence if e is not None and e[attribute_id] is not None]
		for element in newsequence:
			element["_j_appears"] = [e[attribute_id] for e in newsequence].count(element[attribute_id])

		newsequence = [e for e in newsequence if e["_j_appears"] == max(el["_j_appears"] for el in newsequence)]

		newsequence = [e for e in newsequence if e[attribute_count] == max(el[attribute_count] for el in newsequence)]
		return newsequence[0]
	except:
		return None
	finally:
		for e in newsequence:
			del e["_j_appears"]


#	groups = []
#	for element in sequence:
#		for grouprep,groupentries in groups:
#			if grouprep == element[attribute_id]:
#				groupentries.append(element)
#				break
#		else:
#			groups.append((element[attribute_id],[element]))
#
#	groups.sort(key=lambda x:len(x[1]),reverse=True)
#
#	# now group this grouping by number of appearances
#
#	import itertools
#	byappearances = itertools.groupby(groups,key=lambda x:len(x[1]))
#	mostappearances = list(next(byappearances)[1])
#
#	return mostappearances
#	# among those, pick the one with the highest count in one of their appearances


def combine_dicts(dictlist):
	res = {k:d[k] for d in dictlist for k in d}
	return res


def compare_key_in_dicts(key,d1,d2):
	return d1[key] == d2[key]

def alltrue(seq):
	return all(s for s in seq)
