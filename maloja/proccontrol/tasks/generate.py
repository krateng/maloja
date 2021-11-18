import random
import datetime

artists = [
	"Chou Tzuyu","Jennie Kim","Kim Seolhyun","Nancy McDonie","Park Junghwa","Hirai Momo","Rosé Park","Laura Brehm","HyunA",
	"Jeremy Soule","Jerry Goldsmith","Howard Shore","Tilman Sillescu","James Newton Howard","Bear McCreary","David Newman",
	"Approaching Nirvana","7 Minutes Dead","Tut Tut Child","Mr FijiWiji","Tut Tut Child"
]

adjectives = [
	"Black","Pink","Yellow","Scarlet","Purple","Burgundy","Orange","Golden","Green","Vermilion",
	"Misty","Foggy","Cloudy","Hazy","Cold","Hot","Warm","Dark","Bright",
	"Long","Short","Last","First","Final","Huge","Tiny","Important"
]
nouns = [
	"Ship","Princess","Castle","Monastery","Sword","War","Battle","Temple","Army","Horse",
	"Valley","River","Waterfall","Mountain","Tree","Forest","Sea","Desert","Montains","Clouds","Glacier","Sun","Moon",
	"Dusk","Dawn","Twilight","Nightfall","Sunset","Sunrise",
	"Penguin","Tiger","Phoenix","Qilin","Dragon","Tortoise","Bird","Toucan",
	"Area","Region","Land","Span","Gate","Arch","Country","Field",
	"Cherry","Pear","Olive","Apple","Peach","Berry",
	"Sapphire","Emerald","Jade","Ruby"
]
prepositions = ["in","of","over","under","about","across","inside","toward","on","within","with"]
verbs = [
	"Lifting","Stealing","Dancing","Running","Jumping","Singing","Moving","Climbing","Walking","Wandering",
	"Fighting","Entering","Leaving","Meeting","Watching","Eating"
]

patterns = [
	"{n1} {p1} the {a1} {n2}", # Land of the Golden Sun
	"The {a1} {n1}", # The Green Dragon
	"{p1} the {a1} {n1}", # Under the Dark Span
	"{a1} {n1} {p1} the {a2} {n2}",
	"{v1} the {a1} {n1}",
	"{v1} {p1} the {a1} {n1}",
	"{v1} and {v2}",
	"{a1} {n1} {p1} the {n2} {n3}",
	"{a1} {n1} and the {n2} {n3}", # Black Horse and the Cherry Tree
	"{a1} {a2} {p1} your {n1}", # Black Pink in your Area
	"Forward {p1} {n1}"
]

def generate_track():

	title = random.choice(patterns).format(
		n1=random.choice(nouns),
		n2=random.choice(nouns),
		n3=random.choice(nouns),
		a1=random.choice(adjectives),
		a2=random.choice(adjectives),
		p1=random.choice(prepositions),
		p2=random.choice(prepositions),
		v1=random.choice(verbs),
		v2=random.choice(verbs)
	)
	title = "".join([title[0].upper(),title[1:]])
	trackartists = [random.choice(artists) for _ in range(random.randint(1, 3))]

	return {
		"artists":trackartists,
		"title":title
	}



def generate(targetfile):
	with open(targetfile,"a") as fd:
		for _ in range(200):
			track = generate_track()
			for _ in range(random.randint(1, 50)):
				timestamp = random.randint(1, int(datetime.datetime.now().timestamp()))

				entry = "\t".join([str(timestamp),"␟".join(track['artists']),track['title'],"-"])
				fd.write(entry)
				fd.write("\n")
