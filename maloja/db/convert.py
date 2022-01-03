#### ATTENTION ALL ADVENTURERS
#### THIS IS WHAT A SCROBBLE DICT WILL LOOK LIKE FROM NOW ON
#### THIS IS THE SINGLE CANONICAL SOURCE OF TRUTH
#### STOP MAKING DIFFERENT LITTLE DICTS IN EVERY SINGLE FUNCTION
#### THIS IS THE SCHEMA THAT WILL DEFINITELY 100% STAY LIKE THIS AND NOT
#### RANDOMLY GET CHANGED TWO VERSIONS LATER
#### HERE WE GO
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
# 	"origin":string
# }



def scrobble_db_to_dict(resultrow):
	return {
		"time":resultrow.timestamp,
		"track":track_db_to_dict(resultrow.track),
		"duration":resultrow.duration,
		"origin":resultrow.origin
	}

def track_db_to_dict(resultrow):
	return {
		"artists":[],
		"title":resultrow.title,
		"album":{},
		"length":resultrow.length
	}
