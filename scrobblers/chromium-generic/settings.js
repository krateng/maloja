
document.addEventListener("DOMContentLoaded",function() {
	document.getElementById("serverurl").addEventListener("input",updateServer);
	document.getElementById("apikey").addEventListener("input",updateAPIKey);

	document.getElementById("serverurl").addEventListener("change",checkServer);
	document.getElementById("apikey").addEventListener("change",checkServer);

	document.getElementById("serverurl").addEventListener("focusout",checkServer);
	document.getElementById("apikey").addEventListener("focusout",checkServer);


	chrome.runtime.onMessage.addListener(onInternalMessage);


	chrome.storage.local.get({"serverurl":"http://localhost:42010"},function(result) {
		document.getElementById("serverurl").value = result["serverurl"]
		checkServerMaybe()
	});
	chrome.storage.local.get({"apikey":"BlackPinkInYourArea"},function(result) {
		document.getElementById("apikey").value = result["apikey"]
		checkServerMaybe()
	});

	chrome.runtime.sendMessage({"type":"query"})



});


//this makes sure only the second call actually makes a request (the first request is pointless
//when the other element isn't filled yet and might actually overwrite the correct result because
//of a race condition)
var done = 0
function checkServerMaybe() {
	done++;
	if (done == 2) {
		checkServer()
	}
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



function updateServer() {

	text = document.getElementById("serverurl").value


	chrome.storage.local.set({"serverurl":text})
}

function updateAPIKey() {
	text = document.getElementById("apikey").value
	chrome.storage.local.set({"apikey":text})
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
		if ((this.status == 204) || (this.status == 205)) {
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
