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
}

function deleteScrobble(id,element) {
	var callback_func = function(req){
		if (req.status == 200) {
			element.parentElement.parentElement.parentElement.classList.add('removed');
			notifyCallback(req);
		}
		else {
			notifyCallback(req);
		}
	};

	neo.xhttpreq("/apis/mlj_1/delete_scrobble",data={'timestamp':id},method="POST",callback=callback_func,json=true);
}


// EDIT NAME
function editEntity() {

	var namefield = document.getElementById('main_entity_name');
	namefield.contentEditable = "plaintext-only";

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

		callback_func = function(req){
			if (req.status == 200) {
				window.location = "?" + searchParams.toString();
			}
			else {
				notifyCallback(req);
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

function markForMerge() {
	const lcst = window.localStorage;
	var key = "marked_for_merge_" + entity_type;
	var current_stored = (lcst.getItem(key) || '').split(",");
	current_stored = current_stored.filter((x)=>x).map((x)=>parseInt(x));
	current_stored.push(entity_id);
	current_stored = [...new Set(current_stored)];
	lcst.setItem(key,current_stored); //this already formats it correctly
	notify("Success","Marked " + entity_name + " for merge, currently " + current_stored.length + " marked!")
}

function merge() {
	const lcst = window.localStorage;
	var key = "marked_for_merge_" + entity_type;
	var current_stored = lcst.getItem(key).split(",");
	current_stored = current_stored.filter((x)=>x).map((x)=>parseInt(x));

	callback_func = function(req){
		if (req.status == 200) {
			window.location.reload();
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
