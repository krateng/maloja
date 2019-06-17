apikeycorrect = false;

var cookies = {};

function getCookies() {
	cookiestrings = decodeURIComponent(document.cookie).split(';');
	for(var i = 0; i <cookiestrings.length; i++) {
		cookiestrings[i] = cookiestrings[i].trim();
		[key,value] = cookiestrings[i].split("=");
		cookies[key] = value;
	}
}

// always on document load, but call specifically when needed early
document.addEventListener("load",getCookies);

function setCookie(key,val) {
	cookies[key] = val;
	document.cookie = encodeURIComponent(key) + "=" + encodeURIComponent(val);
}
function saveCookies() {
	for (var c in cookies) {
		document.cookie = encodeURIComponent(c) + "=" + encodeURIComponent(cookies[c]);
	}
}



/// RANGE SELECTORS

// in rangeselect.js


/// API KEY



function insertAPIKeyFromCookie() {
	getCookies();
	key = cookies["apikey"];
	document.getElementById("apikey").value = key;
	checkAPIkey()
}

function saveAPIkey() {
	key = APIkey()
	setCookie("apikey",key)
}



function checkAPIkey() {

	url = "/api/test?key=" + APIkey()
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
	if (apikeycorrect) {
		saveAPIkey();
	}
}

function APIkey() {
	return document.getElementById("apikey").value;
}
