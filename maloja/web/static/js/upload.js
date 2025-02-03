function upload(encodedentity,b64) {
	neo.xhttprequest("/apis/mlj_1/addpicture?" + encodedentity,{"b64":b64},"POST")
}
