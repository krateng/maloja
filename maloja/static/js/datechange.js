function datechange() {

	since = document.getElementById("dateselect_from").value;
	to = document.getElementById("dateselect_to").value;

	since = since.split("-").join("/")
	to = to.split("-").join("/")

	//url = window.location.href
	//var url = document.createElement("a")
	//url.href = window.location.href
	//console.log(url.search)

	keys = window.location.search.substring(1).split("&")


	var keydict = {};
	for (var i=0;i<keys.length;i++) {
		kv = keys[i].split("=");
		key = kv[0]
		value = kv[1]
		keydict[key] = value
	}

	delete keydict["in"]
	keydict["since"] = since
	keydict["to"] = to

	console.log(keydict)

	keys = []
	Object.keys(keydict).forEach(function(key) {
		keys.push(key + "=" + keydict[key])
	});
	console.log(keys)

	window.location.href = window.location.protocol
		+ "//" + window.location.hostname
		+ ":" + window.location.port
		+ window.location.pathname
		+ "?" + keys.join("&");

}
