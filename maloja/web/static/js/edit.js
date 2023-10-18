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

// MERGING AND ASSOCIATION

const associate_targets = {
	album: ['artist'],
	track: ['album','artist'],
	artist: []
};

const associate_sources = {
	artist: ['album','track'],
	album: ['track'],
	track: []
};


function getStoredList(key) {
	const lcst = window.sessionStorage;
	var current_stored = (lcst.getItem(key) || '').split(",");
	current_stored = current_stored.filter((x)=>x).map((x)=>parseInt(x));
	return current_stored;
}
function storeList(key,list) {
	const lcst = window.sessionStorage;
	list = [...new Set(list)];
	lcst.setItem(key,list); //this already formats it correctly
}



function markForMerge(element) {
	const parentElement = element.closest('[data-entity_id]');

	var entity_type = parentElement.dataset.entity_type;
	var entity_id = parentElement.dataset.entity_id;
	var entity_name = parentElement.dataset.entity_name;
	entity_id = parseInt(entity_id);

	key = "marked_for_merge_" + entity_type;
	var current_stored = getStoredList(key);
	current_stored.push(entity_id);
	storeList(key,current_stored)

	notify("Marked " + entity_name + " for merge","Currently " + current_stored.length + " marked!")

	toggleMergeIcons(parentElement);
}

function unmarkForMerge(element) {
	const parentElement = element.closest('[data-entity_id]');

	var entity_type = parentElement.dataset.entity_type;
	var entity_id = parentElement.dataset.entity_id;
	var entity_name = parentElement.dataset.entity_name;
	entity_id = parseInt(entity_id);

	var key = "marked_for_merge_" + entity_type;
	var current_stored = getStoredList(key);

	if (current_stored.indexOf(entity_id) > -1) {
		current_stored.splice(current_stored.indexOf(entity_id),1);
		storeList(key,current_stored);
		notify("Unmarked " + entity_name + " from merge","Currently " + current_stored.length + " marked!")

		toggleMergeIcons(parentElement);
	}
	else {
		//notify(entity_name + " was not marked!","")
	}
}

function markForAssociate(element) {
	const parentElement = element.closest('[data-entity_id]');

	var entity_type = parentElement.dataset.entity_type;
	var entity_id = parentElement.dataset.entity_id;
	var entity_name = parentElement.dataset.entity_name;
	entity_id = parseInt(entity_id);


	var key = "marked_for_associate_" + entity_type;
	var current_stored = getStoredList(key);
	current_stored.push(entity_id);
	storeList(key,current_stored);

	notify("Marked " + entity_name + " to add to " + associate_targets[entity_type].join(" or "),"Currently " + current_stored.length + " marked!")

	toggleAssociationIcons(parentElement);

}

function umarkForAssociate(element) {
	const parentElement = element.closest('[data-entity_id]');

	var entity_type = parentElement.dataset.entity_type;
	var entity_id = parentElement.dataset.entity_id;
	var entity_name = parentElement.dataset.entity_name;
	entity_id = parseInt(entity_id);

	var key = "marked_for_associate_" + entity_type;
	var current_stored = getStoredList(key);

	if (current_stored.indexOf(entity_id) > -1) {
		current_stored.splice(current_stored.indexOf(entity_id),1);
		storeList(key,current_stored);

		notify("Unmarked " + entity_name + " from association with " + associate_targets[entity_type].join(" or "),"Currently " + current_stored.length + " marked!")

		toggleAssociationIcons(parentElement);
	}
	else {
		//notify(entity_name + " was not marked!","")
	}

}

function toggleAssociationIcons(element) {
	var entity_type = element.dataset.entity_type;
	var entity_id = element.dataset.entity_id;
	entity_id = parseInt(entity_id);

	var key = "marked_for_associate_" + entity_type;
	var current_stored = getStoredList(key);

	if (current_stored.indexOf(entity_id) > -1) {
		element.classList.add('marked_for_associate');
	} else {
		element.classList.remove('marked_for_associate');
	}

	if (current_stored.length > 0) {
		element.classList.add('somethingmarked_for_associate');
	}
	else {
		element.classList.remove('somethingmarked_for_associate');
	}

	var sourcetypes = associate_sources[entity_type];
	var sourcelist = [];
	for (var src of sourcetypes) {
		var key = "marked_for_associate_" + src;
		sourcelist = sourcelist.concat(getStoredList(key));
	}
	if (sourcelist.length > 0) {
		element.classList.add('sources_marked_for_associate');
	}
	else {
		element.classList.remove('sources_marked_for_associate');
	}

}

function toggleMergeIcons(element) {
	var entity_type = element.dataset.entity_type;
	var entity_id = element.dataset.entity_id;
	entity_id = parseInt(entity_id);

	var key = "marked_for_merge_" + entity_type;
	var current_stored = getStoredList(key);

	if (current_stored.indexOf(entity_id) > -1) {
		element.classList.add('marked_for_merge');
	} else {
		element.classList.remove('marked_for_merge');
	}


	if (current_stored.length > 0) {
		element.classList.add('somethingmarked_for_merge');
	}
	else {
		element.classList.remove('somethingmarked_for_merge');
	}
}

document.addEventListener('DOMContentLoaded',function(){
	var listrows = document.getElementsByClassName('listrow');
	for (var row of listrows) {
		toggleAssociationIcons(row);
		toggleMergeIcons(row); //just for the coloring, no icons
	}
	var topbars = document.getElementsByClassName('iconsubset');
	for (var bar of topbars) {
		toggleAssociationIcons(bar);
		toggleMergeIcons(bar);
	}
})



function merge() {
	var key = "marked_for_merge_" + entity_type;
	var current_stored = getStoredList(key);

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

	storeList(key,[]);
}



function associate(element) {
	const parentElement = element.closest('[data-entity_id]');
	var entity_type = parentElement.dataset.entity_type;
	var entity_id = parentElement.dataset.entity_id;
	entity_id = parseInt(entity_id);

	var requests_todo = 0;
	for (var target_entity_type of associate_sources[entity_type]) {
		var key = "marked_for_associate_" + target_entity_type;
		var current_stored = getStoredList(key);

		if (current_stored.length != 0) {
			requests_todo += 1;
			callback_func = function(req){
				if (req.status == 200) {

					toggleAssociationIcons(parentElement);
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

			storeList(key,[]);
		}

	}

}

function removeAssociate(element) {
	const parentElement = element.closest('[data-entity_id]');
	var entity_type = parentElement.dataset.entity_type;
	var entity_id = parentElement.dataset.entity_id;
	entity_id = parseInt(entity_id);

	var requests_todo = 0;
	for (var target_entity_type of associate_sources[entity_type]) {
		var key = "marked_for_associate_" + target_entity_type;
		var current_stored = getStoredList(key);

		if (current_stored.length != 0) {
			requests_todo += 1;
			callback_func = function(req){
				if (req.status == 200) {

					toggleAssociationIcons(parentElement);
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
					'target_id':entity_id,
					'remove': true
				},
				method="POST",
				callback=callback_func,
				json=true
			);

			storeList(key,[]);
		}

	}
}

function cancelMerge(element) {
	const parentElement = element.closest('[data-entity_id]');

	var entity_type = parentElement.dataset.entity_type;

	var key = "marked_for_merge_" + entity_type;
	storeList(key,[])
	toggleMergeIcons(parentElement);
	notify("Cancelled " + entity_type + " merge!","")
}
function cancelAssociate(element) {
	const parentElement = element.closest('[data-entity_id]');

	var entity_type = parentElement.dataset.entity_type;

	var key = "marked_for_associate_" + entity_type;
	storeList(key,[])
	toggleAssociationIcons(parentElement);
	notify("Cancelled " + entity_type + " association!","")
}
