// JS for all web interface editing / deletion of scrobble data

// HELPERS
function selectAll(e) {
	// https://stackoverflow.com/a/6150060/6651341
	var range = document.createRange();
    range.selectNodeContents(e);
	var sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
}

// DELETION
function toggleDeleteConfirm(element) {
	element.parentElement.parentElement.classList.toggle('active');
	element.parentElement.parentElement.parentElement.classList.toggle('active');
}

function deleteScrobble(id,element) {
	var callback_func = function(req){
		if (req.status == 200) {
			element.parentElement.parentElement.parentElement.parentElement.classList.add('removed');
			notifyCallback(req);
		}
		else {
			notifyCallback(req);
		}
	};

	neo.xhttpreq("/apis/mlj_1/delete_scrobble",data={'timestamp':id},method="POST",callback=callback_func,json=true);
}

// REPARSING

function toggleReparseConfirm(element) {
	element.parentElement.parentElement.classList.toggle('active');
	element.parentElement.parentElement.parentElement.classList.toggle('active');
}

function reparseScrobble(id, element) {
	toggleReparseConfirm(element);

	callback_func = function(req){
		if (req.status == 200) {
			if (req.response.status != 'no_operation') {
				//window.location.reload();
				notifyCallback(req);
				var newtrack = req.response.scrobble.track;
				var row = element.parentElement.parentElement.parentElement.parentElement;
				changeScrobbleRow(row,newtrack);
			}
			else {
				notifyCallback(req);
			}
		}
		else {
			notifyCallback(req);
		}
	};

	neo.xhttpreq("/apis/mlj_1/reparse_scrobble",data={'timestamp':id},method="POST",callback=callback_func,json=true);

}

function changeScrobbleRow(element,newtrack) {
	element.classList.add('changed');

	setTimeout(function(){
		element.getElementsByClassName('track')[0].innerHTML = createTrackCell(newtrack);
	},200);
	setTimeout(function(){element.classList.remove('changed')},300);
}

function createTrackCell(trackinfo) {

	var trackquery = new URLSearchParams();
	trackinfo.artists.forEach((a)=>trackquery.append('artist',a));
	trackquery.append('title',trackinfo.title);

	tracklink = document.createElement('a');
	tracklink.href = "/track?" + trackquery.toString();
	tracklink.textContent = trackinfo.title;

	artistelements = []
	var artistholder = document.createElement('span');
	artistholder.classList.add('artist_in_trackcolumn');
	for (var a of trackinfo.artists) {
		var artistquery = new URLSearchParams();
		artistquery.append('artist',a);

		artistlink = document.createElement('a');
		artistlink.href = "/artist?" + artistquery.toString();
		artistlink.textContent = a;

		artistelements.push(artistlink.outerHTML)
	}

	artistholder.innerHTML = artistelements.join(", ");
	return artistholder.outerHTML + " – " + tracklink.outerHTML;
}


// EDIT NAME
function editEntity() {

	var namefield = document.getElementById('main_entity_name');
	try {
		namefield.contentEditable = "plaintext-only"; // not supported by Firefox
	}
	catch (e) {
		namefield.contentEditable = true;
	}


	namefield.addEventListener('keydown',function(e){
		// dont allow new lines, done on enter
		if (e.key === "Enter") {
			e.preventDefault();
			namefield.blur(); // this leads to below
		}
		// cancel on esc
		else if (e.key === "Escape" || e.key === "Esc") {
			e.preventDefault();
			namefield.textContent = entity_name;
			namefield.blur();
		}
	})

	// emergency, not pretty because it will move cursor
	namefield.addEventListener('input',function(e){
		if (namefield.textContent.includes("\n")) {
			namefield.textContent = namefield.textContent.replace("\n","");
		}
	})

	// manually clicking away OR enter
	namefield.addEventListener('blur',function(e){
		doneEditing();
	})

	namefield.focus();
	selectAll(namefield);
}

function doneEditing() {
	window.getSelection().removeAllRanges();
	var namefield = document.getElementById('main_entity_name');
	namefield.contentEditable = "false";
	newname = namefield.textContent;

	if (newname != entity_name) {
		var searchParams = new URLSearchParams(window.location.search);

		if (entity_type == 'artist') {
			var endpoint = "/apis/mlj_1/edit_artist";
		    searchParams.set("artist", newname);
			var payload = {'id':entity_id,'name':newname};
		}
		else if (entity_type == 'track') {
			var endpoint = "/apis/mlj_1/edit_track";
		    searchParams.set("title", newname);
			var payload = {'id':entity_id,'title':newname}
		}
		else if (entity_type == 'album') {
			var endpoint = "/apis/mlj_1/edit_album";
		    searchParams.set("albumtitle", newname);
			var payload = {'id':entity_id,'albumtitle':newname}
		}

		callback_func = function(req){
			if (req.status == 200) {
				window.location = "?" + searchParams.toString();
			}
			else {
				notifyCallback(req);
				namefield.textContent = entity_name;
			}
		};

		neo.xhttpreq(
			endpoint,
			data=payload,
			method="POST",
			callback=callback_func,
			json=true
		);
	}
}

// MERGING

function showValidMergeIcons() {

	// merge
	const lcst = window.sessionStorage;
	var key = "marked_for_merge_" + entity_type;
	var current_stored = (lcst.getItem(key) || '').split(",");
	current_stored = current_stored.filter((x)=>x).map((x)=>parseInt(x));

	var mergeicon = document.getElementById('mergeicon');
	var mergemarkicon = document.getElementById('mergemarkicon');
	var mergecancelicon = document.getElementById('mergecancelicon');

	mergeicon.classList.add('hide');
	mergemarkicon.classList.add('hide');
	mergecancelicon.classList.add('hide');

	if (current_stored.length == 0) {
		mergemarkicon.classList.remove('hide');
	}
	else {
		mergecancelicon.classList.remove('hide');

		if (current_stored.includes(entity_id)) {

		}
		else {
			mergemarkicon.classList.remove('hide');
			mergeicon.classList.remove('hide');
		}
	}

	// mark for association
	if ((entity_type == 'track') || (entity_type == 'album')) {
		const lcst = window.sessionStorage;
		var key = "marked_for_associate_" + entity_type;
		var current_stored = (lcst.getItem(key) || '').split(",");
		current_stored = current_stored.filter((x)=>x).map((x)=>parseInt(x));

		var associationmarkicon = document.getElementById('associationmarkicon');
		var associationcancelicon = document.getElementById('associationcancelicon');

		associationmarkicon.classList.add('hide');
		associationcancelicon.classList.add('hide');


		if (current_stored.length == 0) {
			associationmarkicon.classList.remove('hide');
		}
		else {
			associationcancelicon.classList.remove('hide');

			if (current_stored.includes(entity_id)) {

			}
			else {
				associationmarkicon.classList.remove('hide');
			}
		}

		if (entity_type == 'track') {
			associationmarkicon.title = "Mark this track to add to album or add artist";
		}
		else {
			associationmarkicon.title = "Mark this album to add artist";
		}
	}



	// association confirm
	if ((entity_type == 'artist') || (entity_type == 'album')) {
		var target_entity_types = {artist:['album','track'], album:['track']};
		var to_associate = {};
		var to_associate_all = [];
		for (var target_entity_type of target_entity_types[entity_type]) {
			const lcst = window.sessionStorage;
			var key = "marked_for_associate_" + target_entity_type;
			var current_stored = (lcst.getItem(key) || '').split(",");
			to_associate[target_entity_type] = current_stored.filter((x)=>x).map((x)=>parseInt(x));
			to_associate_all = to_associate_all.concat(to_associate[target_entity_type]);
		}

		var associateicon = document.getElementById('associate' + entity_type + 'icon');

		associateicon.classList.add('hide');


		if (to_associate_all.length == 0) {

		}
		else {
			associateicon.classList.remove('hide');
			if (entity_type == 'artist') {
				associateicon.title = "Add this artist to " + to_associate['album'].length + " albums and " + to_associate['track'].length + " tracks";
			}
			else {
				associateicon.title = "Add " + to_associate['track'].length + " tracks to this album";
			}

		}
	}





}


function markForMerge() {
	const lcst = window.sessionStorage;
	var key = "marked_for_merge_" + entity_type;
	var current_stored = (lcst.getItem(key) || '').split(",");
	current_stored = current_stored.filter((x)=>x).map((x)=>parseInt(x));
	current_stored.push(entity_id);
	current_stored = [...new Set(current_stored)];
	lcst.setItem(key,current_stored); //this already formats it correctly
	notify("Marked " + entity_name + " for merge","Currently " + current_stored.length + " marked!")
	showValidMergeIcons();
}

function markForAssociate() {
	const lcst = window.sessionStorage;
	var key = "marked_for_associate_" + entity_type;
	var current_stored = (lcst.getItem(key) || '').split(",");
	current_stored = current_stored.filter((x)=>x).map((x)=>parseInt(x));
	current_stored.push(entity_id);
	current_stored = [...new Set(current_stored)];
	lcst.setItem(key,current_stored); //this already formats it correctly
	var whattoadd = ((entity_type == 'track') ? "Artists or Album" : "Artists")
	notify("Marked " + entity_name + " to add " + whattoadd,"Currently " + current_stored.length + " marked!")
	showValidMergeIcons();
}

function merge() {
	const lcst = window.sessionStorage;
	var key = "marked_for_merge_" + entity_type;
	var current_stored = lcst.getItem(key).split(",");
	current_stored = current_stored.filter((x)=>x).map((x)=>parseInt(x));

	callback_func = function(req){
		if (req.status == 200) {
			notifyCallback(req);
			setTimeout(window.location.reload.bind(window.location),1000);
		}
		else {
			notifyCallback(req);
		}
	};

	neo.xhttpreq(
		"/apis/mlj_1/merge_" + entity_type + "s",
		data={
			'source_ids':current_stored,
			'target_id':entity_id
		},
		method="POST",
		callback=callback_func,
		json=true
	);

	lcst.removeItem(key);
}



function associate() {
	const lcst = window.sessionStorage;
	var target_entity_types = {artist:['album','track'], album:['track']};
	var requests_todo = 0;
	for (var target_entity_type of target_entity_types[entity_type]) {
		var key = "marked_for_associate_" + target_entity_type;
		var current_stored = (lcst.getItem(key) || '').split(",");
		current_stored = current_stored.filter((x)=>x).map((x)=>parseInt(x));

		if (current_stored.length != 0) {
			requests_todo += 1;
			callback_func = function(req){
				if (req.status == 200) {

					showValidMergeIcons();
					notifyCallback(req);
					requests_todo -= 1;
					if (requests_todo == 0) {
						setTimeout(window.location.reload.bind(window.location),1000);
					}

				}
				else {
					notifyCallback(req);
				}
			};

			neo.xhttpreq(
				"/apis/mlj_1/associate_" + target_entity_type + "s_to_" + entity_type,
				data={
					'source_ids':current_stored,
					'target_id':entity_id
				},
				method="POST",
				callback=callback_func,
				json=true
			);

			lcst.removeItem(key);
		}

	}

}

function cancelMerge() {
	const lcst = window.sessionStorage;
	var key = "marked_for_merge_" + entity_type;
	lcst.setItem(key,[]);
	showValidMergeIcons();
	notify("Cancelled merge!","")
}
function cancelAssociate() {
	const lcst = window.sessionStorage;
	var key = "marked_for_associate_" + entity_type;
	lcst.setItem(key,[]);
	showValidMergeIcons();
	notify("Cancelled association!","")
}
