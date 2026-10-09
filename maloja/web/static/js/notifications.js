// JS for feedback to the user whenever any XHTTP action is taken

const colors = {
    'error': 'red',
	'warning':'#8ACC26',
	'info':'green'
}

function notification_template(info) {
	const div = document.createElement('div');
	div.className = 'notification';
	div.style.setProperty('--notification-color', colors[info.notification_type]);

	const b = document.createElement('b');
	b.textContent = info.title;

	const span = document.createElement('span');
	span.textContent = info.body;

	div.append(b, document.createElement('br'), span);
	return div;
}

function htmlToElement(html) {
	template = document.createElement('template');
	html = html.trim();
	template.innerHTML = html;
   	return template.content.firstChild;
}

function notify(title,msg,notification_type='info',reload=false) {
	info = {
		'title':title,
		'body':msg,
		'notification_type':notification_type
	}

	var element = notification_template(info);

	document.getElementById('notification_area').append(element);

	setTimeout(function(e){e.remove();},7000,element);
}

function notifyCallback(request) {
	var response = request.response;
	var status = request.status;

	if (status == 200) {
	    if (response.hasOwnProperty('warnings') && response.warnings.length > 0) {
	        var notification_type = 'warning';
	    }
	    else {
	        var notification_type = 'info';
	    }

		var title = "Success!";
		var msg = response.desc || response;
	}
	else {
		var notification_type = 'error';
		var title = "Error: " + response.error.type;
		var msg = response.error.desc || "";
	}


	notify(title,msg,notification_type);
}
