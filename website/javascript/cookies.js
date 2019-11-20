apikeycorrect = false;



/// API KEY
function insertAPIKeyFromCookie() {
	element = document.getElementById("apikey")
	if (element != null && element != undefined) {
		var key = neo.getCookie("apikey");
		if (key != null && key != undefined) {
			element.value = key;
			checkAPIkey();
		}
	}


}

window.addEventListener("load",insertAPIKeyFromCookie);


function saveAPIkey() {
	key = APIkey();
	neo.setCookie("apikey",key,false);
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
