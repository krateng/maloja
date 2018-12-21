
document.addEventListener("DOMContentLoaded",function() {
	document.getElementById("serverurl").addEventListener("input",updateServer);
	document.getElementById("apikey").addEventListener("input",updateAPIKey);
	
	document.getElementById("serverurl").addEventListener("change",checkServer);
	document.getElementById("apikey").addEventListener("change",checkServer);
	
	
	chrome.storage.local.get({"serverurl":"http://localhost:42010"},function(result) {
		document.getElementById("serverurl").value = result["serverurl"]
		checkServer()
	});
	chrome.storage.local.get({"apikey":"BlackPinkInYourArea"},function(result) {
		document.getElementById("apikey").value = result["apikey"]
		checkServer()
	});
	
	
	
});



function updateServer() {
	
	text = document.getElementById("serverurl").value
	
	
	chrome.storage.local.set({"serverurl":text})
}

function updateAPIKey() {
	text = document.getElementById("apikey").value
	chrome.storage.local.set({"apikey":text})
}

function checkServer() {
	url = document.getElementById("serverurl").value + "/db/test?key=" + document.getElementById("apikey").value
	
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
