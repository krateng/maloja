var config_defaults = {
	serverurl:"http://localhost:42010",
	apikey:"BlackPinkInYourArea"
}


document.addEventListener("DOMContentLoaded",function() {

	document.getElementById("serverurl").addEventListener("change",checkServer);
	document.getElementById("apikey").addEventListener("change",checkServer);

	document.getElementById("serverurl").addEventListener("focusout",checkServer);
	document.getElementById("apikey").addEventListener("focusout",checkServer);

	document.getElementById("serverurl").addEventListener("input",saveConfig);
	document.getElementById("apikey").addEventListener("input",saveConfig);


	chrome.runtime.onMessage.addListener(onInternalMessage);

	chrome.storage.local.get(config_defaults,function(result){
		for (var key in result) {
			document.getElementById(key).value = result[key];
		}
		checkServer();
	})

	chrome.runtime.sendMessage({"type":"query"})



});


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



function saveConfig() {
	for (var key in config_defaults) {
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
