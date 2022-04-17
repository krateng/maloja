// JS for feedback to the user whenever any XHTTP action is taken

const colors = {
	'warning':'red',
	'info':'green'
}

const notification_template = info => `
	<div class="notification" style="background-color:${colors[type]};">
		<b>${info.title}</b><br/>
		<span>${info.body}</span>

	</div>
`

function htmlToElement(html) {
	template = document.createElement('template');
	html = html.trim();
	template.innerHTML = html;
   	return template.content.firstChild;
}

function notify(title,msg,type='info',reload=false) {
	info = {
		'title':title,
		'body':msg,
		'type':type
	}

	var element = htmlToElement(notification_template(info));

	document.getElementById('notification_area').append(element);

	setTimeout(function(e){e.remove();},7000,element);
}
