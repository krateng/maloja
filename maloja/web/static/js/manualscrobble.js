var lastArtists = []
var lastTrack = ""


function addArtist(artist) {
	var newartistfield = document.getElementById("artists");
	var artistelement = document.createElement("span");
	artistelement.innerHTML = artist;
	artistelement.style = "padding:5px;";
	document.getElementById("artists_td").insertBefore(artistelement,newartistfield);
	newartistfield.placeholder = "Backspace to remove last"
}

function keyDetect(event) {
	if (event.key === "Enter" || event.key === "Tab") { addEnteredArtist() }
	if (event.key === "Backspace" && document.getElementById("artists").value == "") { removeArtist() }
}

function addEnteredArtist() {
	var newartistfield = document.getElementById("artists");
	var newartist = newartistfield.value.trim();
	newartistfield.value = "";
	if (newartist != "") {
		addArtist(newartist);
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

function clear() {
	document.getElementById("title").value = "";
	document.getElementById("artists").value = "";
	var artists = document.getElementById("artists_td").getElementsByTagName("span")
	while (artists.length > 0) {
			removeArtist();
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
	var title = document.getElementById("title").value;
	scrobble(artists,title);
}

function scrobble(artists,title) {

	lastArtists = artists;
	lastTrack = title;

	var payload = {
		"artists":artists,
		"title":title
	}


	if (title != "" && artists.length > 0) {
		neo.xhttpreq("/apis/mlj_1/newscrobble",data=payload,method="POST",callback=notifyCallback,json=true)
	}

	document.getElementById("title").value = "";
	document.getElementById("artists").value = "";
	var artists = document.getElementById("artists_td").getElementsByTagName("span");
	while (artists.length > 0) {
			removeArtist();
	}
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
		xhttp.open("GET","/apis/mlj_1/search?max=5&query=" + encodeURIComponent(txt), true);
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
