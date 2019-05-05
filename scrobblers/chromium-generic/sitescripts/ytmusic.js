bar = document.querySelector("ytmusic-player-bar")
if (bar == null) {
	console.log("Nothing playing right now!")
	chrome.runtime.sendMessage({type:"stopPlayback",time:Math.floor(Date.now()),artist:"",title:""})
	exit()
}

metadata = bar.querySelector("div[class*=middle-controls] > div[class*=content-info-wrapper]")

ctrl = bar.querySelector("div[class*=left-controls]")

title = metadata.querySelector("yt-formatted-string[class*=title]").getAttribute("title")
artistlist = metadata.querySelector("span > span[class*=subtitle] > yt-formatted-string")
artistelements = artistlist.getElementsByTagName("a")
artists = []
for (var i=0;i<artistelements.length-1;i++) {
	artists.push(artistelements[i].innerHTML)
}
//artist = metadata.querySelector("span > span[class*=subtitle] > yt-formatted-string > a:nth-child(1)").innerHTML
artist = artists.join(";");
duration = ctrl.querySelector("[class*=time-info]").innerHTML.split("/")[1]
if (duration.split(":").length == 2) {
	durationSeconds = parseInt(duration.split(":")[0]) * 60 + parseInt(duration.split(":")[1])
}
else {
	durationSeconds = parseInt(duration.split(":")[0]) * 60 * 60 + parseInt(duration.split(":")[1]) * 60 + parseInt(duration.split(":")[2])
}


control = ctrl.querySelector("div > paper-icon-button[class*=play-pause-button]").getAttribute("title")
if (control == "Play") {
	console.log("Not playing right now")
	chrome.runtime.sendMessage({type:"stopPlayback",time:Math.floor(Date.now()),artist:artist,title:title})
	//stopPlayback()
}
else if (control == "Pause") {
	console.log("Playing " + artist + " - " + title)
	chrome.runtime.sendMessage({type:"startPlayback",time:Math.floor(Date.now()),artist:artist,title:title,duration:durationSeconds})
	//startPlayback(artist,title,durationSeconds)
}
