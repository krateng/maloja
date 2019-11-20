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

function setCookie(key,val,session=true) {
	cookies[key] = val;
	if (!session) {
		var d = new Date();
 		d.setTime(d.getTime() + (500*24*60*60*1000));
		expirestr = "expires=" + d.toUTCString();
	}
	else {
		expirestr = ""
	}
	document.cookie = encodeURIComponent(key) + "=" + encodeURIComponent(val) + ";" + expirestr;
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
	element = document.getElementById("apikey")
	if (element != null && element != undefined) {
		getCookies();
		key = cookies["apikey"];
		if (key != null && key != undefined) {
			element.value = key;
			checkAPIkey();
		}
	}


}

window.addEventListener("load",insertAPIKeyFromCookie);


function saveAPIkey() {
	key = APIkey();
	setCookie("apikey",key,false);
}



function checkAPIkey(extrafunc=null) {

	url = "/api/test?key=" + APIkey()
	var xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = function() {
		if (this.readyState == 4 && (this.status == 204 || this.status == 205)) {
			document.getElementById("apikey").style.backgroundColor = "lawngreen"
			apikeycorrect = true
			saveAPIkey();
		}
		else {
			document.getElementById("apikey").style.backgroundColor = "red"
			apikeycorrect = false
		}

		if (extrafunc != null) {
			extrafunc();
		}

	};
	try {
		xhttp.open("GET",url,true);
		xhttp.send();
	}
	catch (e) {
		document.getElementById("apikey").style.backgroundColor = "red"
		apikeycorrect = false
		if (extrafunc != null) {
			extrafunc();
		}
	}
}

function APIkey() {
	return document.getElementById("apikey").value;
}
