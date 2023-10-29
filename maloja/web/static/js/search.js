var searches = []

function search(searchfield) {
	txt = searchfield.value;
	if (txt == "") {
		reallyclear()
	}
	else {
		xhttp = new XMLHttpRequest();
		searches.push(xhttp)
		xhttp.onreadystatechange = searchresult
		xhttp.open("GET","/api/search?max=5&query=" + encodeURIComponent(txt), true);
		xhttp.send();
	}
}


function html_to_fragment(html) {
	var template = document.createElement("template");
	template.innerHTML = html;
	return template.content;
}

var results_artists;
var results_tracks;
var results_albums;
var searchresultwrap;

window.addEventListener("DOMContentLoaded",function(){
	results_artists = document.getElementById("searchresults_artists");
	results_tracks = document.getElementById("searchresults_tracks");
	results_albums = document.getElementById("searchresults_albums");
	searchresultwrap = document.getElementById("resultwrap");
});

var resulthtml = `
<tr>
	<td class="image"></td>
	<td>
		<span></span><br/>
		<span></span>
	</td>
</tr>
`
const oneresult = html_to_fragment(resulthtml).firstElementChild;




function searchresult() {
	if (this.readyState == 4 && this.status == 200 && document.getElementById("searchinput").value != "" && searches.includes(this)) {
		// any older searches are now rendered irrelevant
		while (searches[0] != this) { searches.splice(0,1) }
		var result = JSON.parse(this.responseText);
		var artists = result["artists"].slice(0,4)
		var tracks = result["tracks"].slice(0,4)
		var albums = result["albums"].slice(0,4)

		while (results_artists.firstChild) {
			results_artists.removeChild(results_artists.firstChild);
		}
		while (results_tracks.firstChild) {
			results_tracks.removeChild(results_tracks.firstChild);
		}
		while (results_albums.firstChild) {
			results_albums.removeChild(results_albums.firstChild);
		}

		for (var i=0;i<artists.length;i++) {
			name = artists[i]["artist"];
			link = artists[i]["link"];
			image = artists[i]["image"];

			var node = oneresult.cloneNode(true);
			node.setAttribute("onclick","goto('" + link + "')");
			node.children[0].style.backgroundImage = "url('" + image + "')";
			node.children[1].children[0].textContent = name;

			results_artists.appendChild(node);
		}
		for (var i=0;i<tracks.length;i++) {

			artists = tracks[i]["track"]["artists"].join(", ");
			title = tracks[i]["track"]["title"];
			link = tracks[i]["link"];
			image = tracks[i]["image"];

			var node = oneresult.cloneNode(true);
			node.setAttribute("onclick","goto('" + link + "')");
			node.children[0].style.backgroundImage = "url('" + image + "')";
			node.children[1].children[0].textContent = artists;
			node.children[1].children[2].textContent = title;

			results_tracks.appendChild(node);
		}
		for (var i=0;i<albums.length;i++) {

			artists = albums[i]["album"].hasOwnProperty("displayArtist") ? albums[i]["album"]["displayArtist"] : albums[i]["album"]["artists"].join(", ");
			albumtitle = albums[i]["album"]["albumtitle"];
			link = albums[i]["link"];
			image = albums[i]["image"];

			var node = oneresult.cloneNode(true);
			node.setAttribute("onclick","goto('" + link + "')");
			node.children[0].style.backgroundImage = "url('" + image + "')";
			node.children[1].children[0].textContent = artists;
			node.children[1].children[2].textContent = albumtitle;

			results_albums.appendChild(node);
		}
		searchresultwrap.classList.remove("hide")

	}
}

function clearresults() {
	window.setTimeout(reallyclear,500)
}
function reallyclear() {
	searchresultwrap.classList.add("hide")
}

function goto(link) {
	window.location = link
}
