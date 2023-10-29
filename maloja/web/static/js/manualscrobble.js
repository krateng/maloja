var lastArtists = [];
var lastTrack = "";
var lastAlbumartists = [];
var lastAlbum = "";


function addArtist(artist) {
	var newartistfield = document.getElementById("artists");
	var artistelement = document.createElement("span");
	artistelement.innerHTML = artist;
	artistelement.style = "padding:5px;";
	document.getElementById("artists_td").insertBefore(artistelement,newartistfield);
	newartistfield.placeholder = "Backspace to remove last"
}
function addAlbumartist(artist) {
	var newartistfield = document.getElementById("albumartists");
	var artistelement = document.createElement("span");
	artistelement.innerHTML = artist;
	artistelement.style = "padding:5px;";
	document.getElementById("albumartists_td").insertBefore(artistelement,newartistfield);
	newartistfield.placeholder = "Backspace to remove last"
}

function keyDetect(event) {
	if (event.key === "Enter" || event.key === "Tab") { addEnteredArtist() }
	if (event.key === "Backspace" && document.getElementById("artists").value == "") { removeArtist() }
}
function keyDetect2(event) {
	if (event.key === "Enter" || event.key === "Tab") { addEnteredAlbumartist() }
	if (event.key === "Backspace" && document.getElementById("albumartists").value == "") { removeAlbumartist() }
}

function addEnteredArtist() {
	var newartistfield = document.getElementById("artists");
	var newartist = newartistfield.value.trim();
	newartistfield.value = "";
	if (newartist != "") {
		addArtist(newartist);
	}
}
function addEnteredAlbumartist() {
	var newartistfield = document.getElementById("albumartists");
	var newartist = newartistfield.value.trim();
	newartistfield.value = "";
	if (newartist != "") {
		addAlbumartist(newartist);
	}
}
function removeArtist() {
	var artists = document.getElementById("artists_td").getElementsByTagName("span")
	var lastartist = artists[artists.length-1]
	document.getElementById("artists_td").removeChild(lastartist);
	if (artists.length < 1) {
		document.getElementById("artists").placeholder = "Separate with Enter"
	}
}
function removeAlbumartist() {
	var artists = document.getElementById("albumartists_td").getElementsByTagName("span")
	var lastartist = artists[artists.length-1]
	document.getElementById("albumartists_td").removeChild(lastartist);
	if (artists.length < 1) {
		document.getElementById("albumartists").placeholder = "Separate with Enter"
	}
}

function clear() {
	document.getElementById("title").value = "";
	document.getElementById("artists").value = "";
	document.getElementById("album").value = "";
	document.getElementById("albumartists").value = "";
	var artists = document.getElementById("artists_td").getElementsByTagName("span")
	while (artists.length > 0) {
			removeArtist();
	}
	var albumartists = document.getElementById("albumartists_td").getElementsByTagName("span")
	while (albumartists.length > 0) {
			removeAlbumartist();
	}
}


function scrobbleIfEnter(event) {
	if (event.key === "Enter") {
		scrobbleNew()
	}
}

function scrobbleNew() {
	var artistnodes = document.getElementById("artists_td").getElementsByTagName("span");
	var artists = [];
	for (let node of artistnodes) {
		artists.push(node.textContent);
	}

	var albumartistnodes = document.getElementById("albumartists_td").getElementsByTagName("span");
	var albumartists = [];
	for (let node of albumartistnodes) {
		albumartists.push(node.textContent);
	}

	if (albumartists.length == 0) {
		var use_track_artists = document.getElementById('use_track_artists_for_album').checked;
		if (use_track_artists) {
			albumartists = null;
		}
	}

	var title = document.getElementById("title").value;
	var album = document.getElementById("album").value;

	if (document.getElementById("use_custom_time").checked) {
		var date = new Date(document.getElementById("scrobble_datetime").value + ':00Z');
		var timestamp = (date.getTime() + (date.getTimezoneOffset() * 60000)) / 1000;
	}
	else {
		var timestamp = null;
	}



	scrobble(artists,title,albumartists,album,timestamp);
}

function scrobble(artists,title,albumartists,album,timestamp) {

	lastArtists = artists;
	lastTrack = title;
	lastAlbum = album;
	lastAlbumartists = albumartists;

	var payload = {
		"artists":artists,
		"title":title,
		"album": album
	}
	if (albumartists != null) {
		payload['albumartists'] = albumartists;
	}
	if (timestamp != null) {
		payload['time'] = timestamp;
	}

	console.log(payload);


	if (title != "" && artists.length > 0) {
		neo.xhttpreq("/apis/mlj_1/newscrobble",data=payload,method="POST",callback=notifyCallback,json=true)
	}

	clear()
}

function scrobbledone(req) {
	result = req.response;
	txt = result["track"]["title"] + " by " + result["track"]["artists"][0];
	if (result["track"]["artists"].length > 1) {
		txt += " et al.";
	}
	document.getElementById("notification").innerHTML = "Scrobbled " + txt + "!";

}

function repeatLast() {
	clear();
	for (let artist of lastArtists) {
		addArtist(artist);
	}
	document.getElementById("title").value = lastTrack;
	for (let artist of lastAlbumartists) {
		addAlbumartist(artist);
	}
	document.getElementById("album").value = lastAlbum;
}



///
// SEARCH
///

function search_manualscrobbling(searchfield) {
	var txt = searchfield.value;
	if (txt == "") {

	}
	else {
		xhttp = new XMLHttpRequest();
		xhttp.onreadystatechange = searchresult_manualscrobbling;
		xhttp.open("GET","/api/search?max=5&query=" + encodeURIComponent(txt), true);
		xhttp.send();
	}
}
function searchresult_manualscrobbling() {
	if (this.readyState == 4 && this.status == 200) {
		document.getElementById("searchresults").innerHTML = "";
		result = JSON.parse(this.responseText);
		tracks = result["tracks"].slice(0,10);
		console.log(tracks);
		for (let t of tracks) {
			track = document.createElement("span");
			trackstr = t.track["artists"].join(", ") + " - " + t.track["title"];
			tracklink = t["link"];
			track.innerHTML = "<a href='" + tracklink + "'>" +  trackstr + "</a>";
			row = document.createElement("tr")
			col1 = document.createElement("td")
			button = document.createElement("button")
			button.innerHTML = "Scrobble!"
			button.onclick = function(){ scrobble(t.track["artists"],t.track["title"])};
			col2 = document.createElement("td")
			row.appendChild(col1)
			col1.appendChild(button)
			row.appendChild(col2)
			col2.appendChild(track)
			document.getElementById("searchresults").appendChild(row);
		}


	}
}
