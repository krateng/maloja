apikeycorrect = false;

function insertAPIKeyFromCookie() {
	cookies = decodeURIComponent(document.cookie).split(';');
	for(var i = 0; i <cookies.length; i++) {
		cookies[i] = cookies[i].trim()
		if (cookies[i].startsWith("apikey=")) {
			document.getElementById("apikey").value = cookies[i].replace("apikey=","")
			checkAPIkey()
		}
	}
}


function saveAPIkey() {
	key = document.getElementById("apikey").value
	document.cookie = "apikey=" + encodeURIComponent(key)
}



function checkAPIkey() {
	saveAPIkey()
	url = "/db/test?key=" + document.getElementById("apikey").value
	var xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = function() {
		if (this.readyState == 4 && (this.status == 204 || this.status == 205)) {
			document.getElementById("apikey").style.backgroundColor = "lawngreen"
			apikeycorrect = true
		}
		else {
			document.getElementById("apikey").style.backgroundColor = "red"
			apikeycorrect = false
		}
	};
	try {
		xhttp.open("GET",url,true);
		xhttp.send();
	}
	catch (e) {
		document.getElementById("apikey").style.backgroundColor = "red"
		apikeycorrect = false
	}
}
