

chrome.tabs.onUpdated.addListener(onTabUpdated);
chrome.tabs.onRemoved.addListener(onTabRemoved);
chrome.runtime.onMessage.addListener(onPlaybackUpdate);


var patterns = [
	"https://music.youtube.com",
	"http://music.youtube.com"
];

function onTabUpdated(tabId, changeInfo, tab) {
	if (changeInfo.status !== "complete") {
		return;
	}
	console.log("Update")
	chrome.tabs.get(tabId,party)
}

function onTabRemoved() {

}



function party(tab) {

	importantPage = false

	for (var i=0;i<patterns.length;i++) {
		if (tab.url.startsWith(patterns[i])) {
			importantPage = true

		}
	}

	if (importantPage) {
		window.setTimeout(function(){chrome.tabs.executeScript(tab.id,{"file":"contentScript.js"})},1000); // youtube for some reason decides to not update the artist immediately
	}
}


function onPlaybackUpdate(request,sender) {
	//console.log("Got update from Plex Web!")
	if (request.type == "stopPlayback" && currentlyPlaying) {
		stopPlayback(request.artist,request.title);
	}
	else if (request.type == "startPlayback") {
		startPlayback(request.artist,request.title,request.duration);
	}
}

var currentTitle;
var currentArtist;
var currentLength;
var alreadyPlayed;
var currentlyPlaying = false;
var lastUpdate = 0;
var alreadyScrobbled = false;


function startPlayback(artist,title,seconds) {


	// CASE 1: Resuming playback of previously played title
	if (artist == currentArtist && title == currentTitle && !currentlyPlaying) {
		console.log("Resuming playback")

		// Already played full song
		while (alreadyPlayed > currentLength) {
			alreadyPlayed = alreadyPlayed - currentLength
			scrobble(currentArtist,currentTitle,currentLength)
		}

		setUpdate()
		currentlyPlaying = true

	}

	// CASE 2: New track is being played
	else if (artist != currentArtist || title != currentTitle) {

		//first inform ourselves that the previous track has now been stopped for good
		stopPlayback(artist,title)
		//then initialize new playback
		console.log("New track")
		setUpdate()
		alreadyPlayed = 0
		currentTitle = title
		currentArtist = artist
		currentLength = seconds
		console.log(artist + " - " + title + " is playing!")
		currentlyPlaying = true
	}
}

// the artist and title arguments are not attributes of the track being stopped, but of the track active now
// they are here to recognize whether the playback has been paused or completely ended / replaced
function stopPlayback(artist,title) {

	//CASE 1: Playback just paused OR CASE 2: Playback ended
	if (currentlyPlaying) {
		d = setUpdate()
		alreadyPlayed = alreadyPlayed + d
		console.log(d + " seconds played since last update, " + alreadyPlayed + " seconds played overall")
	}


	// Already played full song
	while (alreadyPlayed > currentLength) {
		alreadyPlayed = alreadyPlayed - currentLength
		scrobble(currentArtist,currentTitle,currentLength)
	}

	currentlyPlaying = false



	//ONLY CASE 2: Playback ended
	if (artist != currentArtist || title != currentTitle) {
		if (alreadyPlayed > currentLength / 2) {
			scrobble(currentArtist,currentTitle,alreadyPlayed)
			alreadyPlayed = 0
		}
	}
}


// One problem here: Closing the player while it's paused does not cause an event, so the track will only be scrobbled the next time we play something.
// Also potentially problematic: Pausing a track and just leaving it should probably trigger a scrobble after some time because we can assume the user just stopped listening but didn't bother to press the X
// We could simply check for scrobblability when the track is paused, but this would remove the ability to send listening time with the scrobble


function ostopPlayback(artist,title) {
	currentlyPlaying = false
	console.log("Playback stopped!")
	d = new Date()
	t = Math.floor(d.getTime()/1000)
	delta = t - lastUpdate
	console.log("Since the last update, " + delta + " seconds of music have been played")
	alreadyPlayed = alreadyPlayed + delta
	console.log(alreadyPlayed + " seconds of this track have been played overall")
	if ((alreadyPlayed > currentLength/2) && !alreadyScrobbled) {
		console.log("Enough to scrobble: " + currentArtist + " - " + currentTitle)
		scrobble(currentArtist,currentTitle)
		alreadyScrobbled = true
	}
}

function ostartPlayback(artist,title,seconds) {

	console.log("Playback started!")
	if (artist == currentArtist && title == currentTitle && !currentlyPlaying) {
		console.log("Still previous track!")
		while (alreadyPlayed > currentLength) {
			console.log("This song is being played several times in a row!")
			if (!alreadyScrobbled) {
				scrobble(currentArtist,currentTitle)
				//alreadyScrobbled = true
			}
			alreadyPlayed = alreadyPlayed - currentLength
			alreadyScrobbled = false

		}
		d = new Date()
		t = Math.floor(d.getTime()/1000)
		lastUpdate = t
		currentlyPlaying = true
	}
	else if (artist != currentArtist || title != currentTitle) {
		console.log("New track!")
		if (currentlyPlaying) {
			console.log("We were playing another track before, so let's check if we should scrobble that.")
			d = new Date()
			t = Math.floor(d.getTime()/1000)
			delta = t - lastUpdate
			console.log("Since the last update, " + delta + " seconds of music have been played")
			alreadyPlayed = alreadyPlayed + delta

		}

		console.log("The previous track was played for " + alreadyPlayed + " seconds, that's " + Math.floor(alreadyPlayed/currentLength * 100) + "% of its length.")
		if (alreadyPlayed > currentLength/2 && !alreadyScrobbled) {
			console.log("Enough to scrobble: " + currentArtist + " - " + currentTitle)
			scrobble(currentArtist,currentTitle)

		}
		else if (alreadyScrobbled) {
			console.log("We already scrobbled this track tho.")
			alreadyScrobbled = false
		}


		console.log("But now, new track!")
		d = new Date()
		t = Math.floor(d.getTime()/1000)
		lastUpdate = t
		alreadyPlayed = 0
		currentTitle = title
		currentArtist = artist
		currentLength = seconds
		console.log(artist + " - " + title + " is playing!")
		currentlyPlaying = true
	}
}



function scrobble(artist,title,seconds) {
	console.log("Scrobbling " + artist + " - " + title + "; " + seconds + " seconds playtime")
	artiststring = encodeURIComponent(artist)
	titlestring = encodeURIComponent(title)
	chrome.storage.local.get("apikey",function(result) {
		APIKEY = result["apikey"]
		chrome.storage.local.get("serverurl",function(result) {
			URL = result["serverurl"]
			var xhttp = new XMLHttpRequest();
			xhttp.open("POST",URL + "/db/newscrobble",true);
			xhttp.send("artist=" + artiststring + "&title=" + titlestring + "&duration=" + seconds + "&key=" + APIKEY)
		});
	});


}

function setUpdate() {
	d = new Date()
	t = Math.floor(d.getTime()/1000)
	delta = t - lastUpdate
	lastUpdate = t
	return delta
}
