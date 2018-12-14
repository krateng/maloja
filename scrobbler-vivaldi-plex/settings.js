
document.addEventListener("DOMContentLoaded",function() {
	document.getElementById("serverurl").addEventListener("input",updateServer);
	document.getElementById("apikey").addEventListener("input",updateAPIKey);
	
	
	chrome.storage.local.get({"serverurl":"http://localhost:42010"},function(result) {
		document.getElementById("serverurl").value = result["serverurl"]
	});
	chrome.storage.local.get({"apikey":"BlackPinkInYourArea"},function(result) {
		document.getElementById("apikey").value = result["apikey"]
	});
	
});



function updateServer() {
	
	text = document.getElementById("serverurl").value
	
	if (!text.startsWith("http://") & !text.startsWith("https://")) {
		document.getElementById("serverurl").style.backgroundColor = "pink";
	}
	else {
		document.getElementById("serverurl").style.backgroundColor = "white";
		chrome.storage.local.set({"serverurl":text})
	}
}

function updateAPIKey() {
	text = document.getElementById("apikey").value
	chrome.storage.local.set({"apikey":text})
}
