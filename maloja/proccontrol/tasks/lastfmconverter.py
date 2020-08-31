import os, datetime, re
from ...cleanup import *
from ...utilities import *




c = CleanerAgent()



def convert(input,output):

	with open(input,"r",encoding="utf-8") as log:
		with open(output,"w") as outputlog:


			stamps = [99999999999999]

			for l in log:
				l = l.replace("\n","")
				data = l.split(",")

				artist = data[0]
				album = data[1]
				title = data[2]
				time = data[3]


				(artists,title) = c.fullclean(artist,title)

				artistsstr = "␟".join(artists)


				timeparts = time.split(" ")
				(h,m) = timeparts[3].split(":")

				months = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,"Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}

				timestamp = int(datetime.datetime(int(timeparts[2]),months[timeparts[1]],int(timeparts[0]),int(h),int(m)).timestamp())


				## We prevent double timestamps in the database creation, so we technically don't need them in the files
				## however since the conversion from lastfm to maloja is a one-time thing, we should take any effort to make the file as good as possible
				if (timestamp < stamps[-1]):
					pass
				elif (timestamp == stamps[-1]):
					timestamp -= 1
				else:
					while(timestamp in stamps):
						timestamp -= 1

				if (timestamp < stamps[-1]):
					stamps.append(timestamp)
				else:
					stamps.insert(0,timestamp)


				entry = "\t".join([str(timestamp),artistsstr,title,album])
				entry = entry.replace("#",r"\num")

				outputlog.write(entry)
				outputlog.write("\n")
