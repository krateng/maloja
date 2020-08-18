function upload(encodedentity,b64) {
	neo.xhttprequest("/api/addpicture?" + encodedentity,{"b64":b64},"POST")
}
