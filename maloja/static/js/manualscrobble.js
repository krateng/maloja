function keyDetect(event) {
	if (event.key === "Enter" || event.key === "Tab") { addArtist() }
	if (event.key === "Backspace" && document.getElementById("artists").value == "") { removeArtist() }
}

function addArtist() {
	element = document.getElementById("artists");
	newartist = element.value.trim();
	element.value = "";
	if (newartist != "") {
		artist = document.createElement("span");
		artist.innerHTML = newartist;
		artist.style = "padding:5px;";
		document.getElementById("artists_td").insertBefore(artist,element);

		element.placeholder = "Backspace to remove last"
	}
}
function removeArtist() {
	artists = document.getElementById("artists_td").getElementsByTagName("span")
	lastartist = artists[artists.length-1]
	document.getElementById("artists_td").removeChild(lastartist);
	if (artists.length < 1) {
		document.getElementById("artists").placeholder = "Separate with Enter"
	}
}


function scrobbleIfEnter(event) {
	if (event.key === "Enter") {
		scrobbleNew()
	}
}

function scrobbleNew() {
	artistnodes = document.getElementById("artists_td").getElementsByTagName("span");
	artists = [];
	for (let node of artistnodes) {
		artists.push(node.innerHTML);
	}
	title = document.getElementById("title").value;
	scrobble(artists,title);
}

function scrobble(artists,title) {


	artist = artists.join(";");

	if (title != "" && artists.length > 0) {
		xhttp = new XMLHttpRequest();
		xhttp.onreadystatechange = scrobbledone
		xhttp.open("GET","/api/newscrobble?artist=" + encodeURIComponent(artist) +
			"&title=" + encodeURIComponent(title), true);
		xhttp.send();
	}

	document.getElementById("title").value = "";
	document.getElementById("artists").value = "";
	parent = document.getElementById("artists_td");
	artists = document.getElementById("artists_td").getElementsByTagName("span")
	while (artists.length > 0) {
			removeArtist();
	}
}

function scrobbledone() {
	if (this.readyState == 4 && this.status == 200) {
		result = JSON.parse(this.responseText);
		txt = result["track"]["title"] + " by " + result["track"]["artists"][0];
		if (result["track"]["artists"].length > 1) {
			txt += " et al.";
		}
		document.getElementById("notification").innerHTML = "Scrobbled " + txt + "!";
	}

}




///
// SEARCH
///

function search_manualscrobbling(searchfield) {
	txt = searchfield.value;
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
			trackstr = t["artists"].join(", ") + " - " + t["title"];
			tracklink = t["link"];
			track.innerHTML = "<a href='" + tracklink + "'>" +  trackstr + "</a>";
			row = document.createElement("tr")
			col1 = document.createElement("td")
			col1.className = "button"
			col1.innerHTML = "Scrobble!"
			col1.onclick = function(){ scrobble(t["artists"],t["title"])};
			col2 = document.createElement("td")
			row.appendChild(col1)
			row.appendChild(col2)
			col2.appendChild(track)
			document.getElementById("searchresults").appendChild(row);
		}


	}
}
