function getxpath(path,type) {
	result = document.evaluate(path, this, null, type, null);

	if (type == XPathResult.FIRST_ORDERED_NODE_TYPE) {
		return result.singleNodeValue;
	}
	else if (type == XPathResult.ORDERED_NODE_ITERATOR_TYPE) {
		resultarray = [];
		while(node = result.iterateNext()) {
	  		resultarray.push(node);
		}

		return resultarray;
	}
	else if (type == XPathResult.STRING_TYPE) {
		return result.stringValue;
	}

//	if (path.split("/").slice(-1)[0].startsWith("text()") || path.split("/").slice(-1)[0].startsWith("@")) {
//		result = document.evaluate(path, this, null, XPathResult.STRING_TYPE, null);
//		return result.stringValue;
//	}
//	else {
//		result = document.evaluate(path, this, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
//		return result.singleNodeValue;
//	}


}
Node.prototype.xpath = getxpath;


bar = document.xpath(maloja_scrobbler_selector_playbar, XPathResult.FIRST_ORDERED_NODE_TYPE);
if (bar == null) {
	console.log("[Maloja Scrobbler] Nothing playing right now!");
	chrome.runtime.sendMessage({type:"stopPlayback",time:Math.floor(Date.now()),artist:"",title:""});
}
else {
	metadata = bar.xpath(maloja_scrobbler_selector_metadata, XPathResult.FIRST_ORDERED_NODE_TYPE);
	duration = bar.xpath(maloja_scrobbler_selector_duration, XPathResult.STRING_TYPE);
	duration = duration + '';


	title = metadata.xpath(maloja_scrobbler_selector_title, XPathResult.STRING_TYPE);
	if (typeof maloja_scrobbler_selector_artists !== "undefined") {
		artistnodes = metadata.xpath(maloja_scrobbler_selector_artists, XPathResult.ORDERED_NODE_ITERATOR_TYPE);
		artists = artistnodes.map(x => x.xpath(maloja_scrobbler_selector_artist, XPathResult.STRING_TYPE));
		artist = artists.join(";");
	}
	else {
		artist = metadata.xpath(maloja_scrobbler_selector_artist, XPathResult.STRING_TYPE);
	}


	if (typeof duration_needs_split !== "undefined" && duration_needs_split) {
		duration = duration.split("/").slice(-1)[0].trim();
	}

	if (duration.split(":").length == 2) {
		durationSeconds = parseInt(duration.split(":")[0]) * 60 + parseInt(duration.split(":")[1]);
	}
	else {
		durationSeconds = parseInt(duration.split(":")[0]) * 60 * 60 + parseInt(duration.split(":")[1]) * 60 + parseInt(duration.split(":")[2]);
	}


	control = bar.xpath(maloja_scrobbler_selector_control, XPathResult.STRING_TYPE);
	try {
		label_playing = maloja_scrobbler_label_playing
	}
	catch {
		label_playing = "Pause"
	}
	try {
		label_paused = maloja_scrobbler_label_paused
	}
	catch {
		label_paused = "Play"
	}
	if (control == label_paused) {
		console.log("[Maloja Scrobbler] Not playing right now");
		chrome.runtime.sendMessage({type:"stopPlayback",time:Math.floor(Date.now()),artist:artist,title:title});
		//stopPlayback()
	}
	else if (control == label_playing) {
		console.log("[Maloja Scrobbler] Playing " + artist + " - " + title + " (" + durationSeconds + " sec)");
		chrome.runtime.sendMessage({type:"startPlayback",time:Math.floor(Date.now()),artist:artist,title:title,duration:durationSeconds});
		//startPlayback(artist,title,durationSeconds)
	}

}
