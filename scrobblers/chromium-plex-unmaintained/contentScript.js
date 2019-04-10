bar = document.querySelector("div[class*=PlayerControls]")
if (bar == null) {
	console.log("Nothing playing right now!")
	chrome.runtime.sendMessage({type:"stopPlayback",artist:"",title:""})
	exit()
}

metadata = bar.querySelector("div[class*=PlayerControlsMetadata-container]")

title = metadata.querySelector("a[class*=MetadataPosterTitle-singleLineTitle]").getAttribute("title")
artist = metadata.querySelector("span[class*=MetadataPosterTitle-title] > a:nth-child(1)").getAttribute("title")
duration = metadata.querySelector("[data-qa-id=mediaDuration]").innerHTML.split("/")[1]
if (duration.split(":").length == 2) {
	durationSeconds = parseInt(duration.split(":")[0]) * 60 + parseInt(duration.split(":")[1])
}
else {
	durationSeconds = parseInt(duration.split(":")[0]) * 60 * 60 + parseInt(duration.split(":")[1]) * 60 + parseInt(duration.split(":")[2])
}


control = bar.querySelector("div[class*=PlayerControls-buttonGroupCenter] > button:nth-child(2)").getAttribute("title")
if (control == "Play") {
	console.log("Not playing right now")
	chrome.runtime.sendMessage({type:"stopPlayback",artist:artist,title:title})
	//stopPlayback()
}
else if (control == "Pause") {
	console.log("Playing " + artist + " - " + title)
	chrome.runtime.sendMessage({type:"startPlayback",artist:artist,title:title,duration:durationSeconds})
	//startPlayback(artist,title,durationSeconds)
}







