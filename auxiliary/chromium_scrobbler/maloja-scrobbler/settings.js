// duplicate this info for now, don't know if there is a better way than sending messages
var pages = {
	"plex":"Plex",
	"ytmusic":"YouTube Music",
	"spotify":"Spotify",
	"bandcamp":"Bandcamp",
	"soundcloud":"Soundcloud",
	"navidrome":"Navidrome"
}

var config_defaults = {
	serverurl:"http://localhost:42010",
	apikey:"BlackPinkInYourArea"
}

for (var key in pages) {
	config_defaults["service_active_" + key] = true;
}


document.addEventListener("DOMContentLoaded",function() {

	var sitelist = document.getElementById("sitelist");


	for (var identifier in pages) {
		sitelist.append(document.createElement('br'));
		var checkbox = document.createElement('input');
		checkbox.type = "checkbox";
		checkbox.id = "service_active_" + identifier;
		var label = document.createElement('label');
		label.for = checkbox.id;
		label.textContent = pages[identifier];
		sitelist.appendChild(checkbox);
		sitelist.appendChild(label);

		checkbox.addEventListener("change",toggleSite);

	}



	document.getElementById("serverurl").addEventListener("change",checkServer);
	document.getElementById("apikey").addEventListener("change",checkServer);

	document.getElementById("serverurl").addEventListener("focusout",checkServer);
	document.getElementById("apikey").addEventListener("focusout",checkServer);

	document.getElementById("serverurl").addEventListener("input",saveServer);
	document.getElementById("apikey").addEventListener("input",saveServer);


	chrome.runtime.onMessage.addListener(onInternalMessage);

	chrome.storage.local.get(config_defaults,function(result){
		console.log(result);
		for (var key in result) {

			// booleans
			if (result[key] == true || result[key] == false) {
				document.getElementById(key).checked = result[key];
			}

			// text
			else{
				document.getElementById(key).value = result[key];
			}

		}
		checkServer();
	})

	chrome.runtime.sendMessage({"type":"query"})



});

function toggleSite(evt) {
	var element = evt.target;
	chrome.storage.local.set({ [element.id]: element.checked });
}


function onInternalMessage(request,sender) {
	if (request.type == "response") {
		players = request.content
		html = "";
		for (var i=0;i<players.length;i++) {
			if (players[i][1]) {
				html += "<li>" + players[i][0] + ": " + players[i][1] + " - " + players[i][2]
			}
			else {
				html += "<li>" + players[i][0] + ": Playing nothing"
			}
		}
		document.getElementById("playinglist").innerHTML = html;
	}
}



function saveServer() {
	for (var key of ["serverurl","apikey"]) {
		var value = document.getElementById(key).value;
		chrome.storage.local.set({ [key]: value });
	}
}

function checkServer() {
	url = document.getElementById("serverurl").value + "/api/test?key=" + document.getElementById("apikey").value

	var xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = createCheckmarks;
	try {
		xhttp.open("GET",url,true);
		xhttp.send();
	}
	catch (e) {
		//document.getElementById("checkmark_url").innerHTML = "❌"
		//document.getElementById("checkmark_key").innerHTML = "❌"
		document.getElementById("serverurl").style.backgroundColor = "red"
		document.getElementById("apikey").style.backgroundColor = "red"
	}

}

function createCheckmarks() {
	if (this.readyState == 4) {
		if ((this.status >= 200) && (this.status < 300)) {
			//document.getElementById("checkmark_url").innerHTML = "✔️"
			//document.getElementById("checkmark_key").innerHTML = "✔️"
			document.getElementById("serverurl").style.backgroundColor = "lawngreen"
			document.getElementById("apikey").style.backgroundColor = "lawngreen"
		}
		else if (this.status == 403) {
			//document.getElementById("checkmark_url").innerHTML = "✔️"
			//document.getElementById("checkmark_key").innerHTML = "❌"
			document.getElementById("serverurl").style.backgroundColor = "lawngreen"
			document.getElementById("apikey").style.backgroundColor = "red"
		}
		else {
			//document.getElementById("checkmark_url").innerHTML = "❌"
			//document.getElementById("checkmark_key").innerHTML = "❌"
			document.getElementById("serverurl").style.backgroundColor = "red"
			document.getElementById("apikey").style.backgroundColor = "red"
		}
	}
}
