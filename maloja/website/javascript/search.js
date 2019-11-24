function search(searchfield) {
	txt = searchfield.value;
	if (txt == "") {
		reallyclear()
	}
	else {
		xhttp = new XMLHttpRequest();
		xhttp.onreadystatechange = searchresult
		xhttp.open("GET","/api/search?max=5&query=" + encodeURIComponent(txt), true);
		xhttp.send();
	}
}
function searchresult() {
	if (this.readyState == 4 && this.status == 200 && document.getElementById("searchinput").value != "") {
		// checking if field is empty in case we get an old result coming in that would overwrite our cleared result window
		result = JSON.parse(this.responseText);
		artists = result["artists"].slice(0,5)
		tracks = result["tracks"].slice(0,5)
		html = `<div class="searchresults">
				<span>Artists</span>
				<table class="searchresults_artists">`

				for (var i=0;i<artists.length;i++) {
					name = artists[i]["name"];
					link = artists[i]["link"];
					image = artists[i]["image"];

					html += `<tr onclick="goto('` + link + `')">
						<td class="image" style="background-image:url('` + image + `');"></td>
						<td>
							<span>` + name + `</span><br/>
						</td>
					</tr>`
				}

				html += `</table>
				<br/><br/>
				<span>Tracks</span>
				<table class="searchresults_tracks">`

				for (var i=0;i<tracks.length;i++) {

					artists = tracks[i]["artists"].join(", ");
					title = tracks[i]["title"];
					link = tracks[i]["link"];
					image = tracks[i]["image"];

					html += `<tr onclick="goto('` + link + `')">
						<td class="image" style="background-image:url('` + image + `');"></td>
						<td>
							<span>` + artists + `</span><br/>
							<span>` + title + `</span>
						</td>
					</tr>`

				}

				html += `</table>
			</div>`


			document.getElementById("resultwrap").innerHTML = html;
	}
}

		function clearresults() {
			window.setTimeout(reallyclear,500)
		}
		function reallyclear() {
			document.getElementById("resultwrap").innerHTML = "";
		}

		function goto(link) {
			window.location = link
}
