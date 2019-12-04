function upload(encodedentity,apikey,b64) {
	neo.xhttprequest("/api/addpicture?key=" + apikey + "&" + encodedentity,{"b64":b64},"POST")
}
