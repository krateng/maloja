localStorage = window.localStorage;

function showRange(identifier,unit) {
	// Make all modules disappear
	modules = document.getElementsByClassName("stat_module_" + identifier);
	for (var i=0;i<modules.length;i++) {
		//modules[i].setAttribute("style","width:0px;overflow:hidden;")
		// cheesy trick to make the allocated space always whatever the biggest module needs
		// somehow that messes up pulse on the start page tho
		modules[i].setAttribute("style","display:none;");
	}

	// Make requested module appear
	reactivate = document.getElementsByClassName(identifier + "_" + unit);
	for (var i=0;i<reactivate.length;i++) {
		reactivate[i].setAttribute("style","");
	}

	// Set all selectors to unselected
	selectors = document.getElementsByClassName("stat_selector_" + identifier);
	for (var i=0;i<selectors.length;i++) {
		selectors[i].setAttribute("style","");
	}

	// Set the active selector to selected
	reactivate = document.getElementsByClassName("selector_" + identifier + "_" + unit);
	for (var i=0;i<reactivate.length;i++) {
		reactivate[i].setAttribute("style","opacity:0.5;");
	}

	links = document.getElementsByClassName("stat_link_" + identifier);
	for (let l of links) {
		var a = l.href.split("=");
		a.splice(-1);
		a.push(unit);
		l.href = a.join("=");
	}

}

function showRangeManual(identifier,unit) {
	showRange(identifier,unit);
	//neo.setCookie("rangeselect_" + identifier,unit);
	localStorage.setItem("rangeselect_" + identifier,unit);
}



document.addEventListener('DOMContentLoaded',function() {
	for (let type of ["topartists","toptracks","pulse"]) {
		var val = localStorage.getItem("rangeselect_" + type);
		if (val != null) {
			showRange(type,val);
		}
		else {
			var val = neo.getCookie("rangeselect_" + type);
			if (val != undefined) {
				showRangeManual(type,val);	//sets local storage
			}
		}


	}
})
