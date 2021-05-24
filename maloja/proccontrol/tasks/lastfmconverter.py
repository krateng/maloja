import os, datetime, re
from ...cleanup import *
from doreah.io import col
#from ...utilities import *




c = CleanerAgent()



def convert(input,output):

	with open(input,"r",encoding="utf-8") as log:
		with open(output,"w") as outputlog:


			stamps = [99999999999999]

			success = 0
			failed = 0
			for l in log:
				l = l.replace("\n","")
				try:
					artist,album,title,time = l.split(",")
				except KeyboardInterrupt:
					raise
				except:
					print(col['red']("Line '" + l + "' does not look like a valid entry. Scrobble not imported."))
					failed += 1
					continue

				try:
					(artists,title) = c.fullclean(artist,title)
					artistsstr = "␟".join(artists)

					timeparts = time.split(" ")
					(h,m) = timeparts[3].split(":")

					months = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,"Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}
					timestamp = int(datetime.datetime(int(timeparts[2]),months[timeparts[1]],int(timeparts[0]),int(h),int(m)).timestamp())


					## We prevent double timestamps in the database creation, so we technically don't need them in the files
					## however since the conversion from lastfm to maloja is a one-time thing, we should take any effort to make
					## the file as good as possible
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
				except KeyboardInterrupt:
					raise
				except:
					print(col['red']("Line '" + l + "' could not be parsed. Scrobble not imported."))
					failed += 1
					continue


				entry = "\t".join([str(timestamp),artistsstr,title,album])

				outputlog.write(entry)
				outputlog.write("\n")

				success += 1

				if success % 100 == 0:
					print("Imported " + str(success) + " scrobbles...")

			return (success,failed)
