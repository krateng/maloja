import sys, os, datetime, re, cleanup

log = open(sys.argv[1])

outputlog = open(sys.argv[2],"a")

for l in log:
	l = l.replace("\n","")
	data = l.split(",")
	
	artist = data[0]
	album = data[1]
	title = data[2]
	time = data[3]
	

	(artists,title) = cleanup.fullclean(artist,title)
	
	artistsstr = "␟".join(artists)
	
	
	timeparts = time.split(" ")
	(h,m) = timeparts[3].split(":")
	
	months = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,"Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}
	
	timestamp = int(datetime.datetime(int(timeparts[2]),months[timeparts[1]],int(timeparts[0]),int(h),int(m)).timestamp())
	
	entry = "\t".join([str(timestamp),artistsstr,title,album])
	
	
	outputlog.write(entry)
	outputlog.write("\n")
	
	


