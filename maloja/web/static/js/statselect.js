localStorage = window.localStorage;

function showStats(identifier,unit) {
	// Make all modules disappear
	var modules = document.getElementsByClassName("stat_module_" + identifier);
	for (var i=0;i<modules.length;i++) {
		//modules[i].setAttribute("style","width:0px;overflow:hidden;")
		// cheesy trick to make the allocated space always whatever the biggest module needs
		// somehow that messes up pulse on the start page tho
		modules[i].setAttribute("style","display:none;");
	}

	// Make requested module appear
	var reactivate = document.getElementsByClassName(identifier + "_" + unit);
	for (var i=0;i<reactivate.length;i++) {
		reactivate[i].setAttribute("style","");
	}

	// Set all selectors to unselected
	var selectors = document.getElementsByClassName("stat_selector_" + identifier);
	for (var i=0;i<selectors.length;i++) {
		selectors[i].setAttribute("style","");
	}

	// Set the active selector to selected
	var reactivate = document.getElementsByClassName("selector_" + identifier + "_" + unit);
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


function showStatsManual(identifier,unit) {
	showStats(identifier,unit);
	//neo.setCookie("rangeselect_" + identifier,unit);
	localStorage.setItem("statselect_" + identifier,unit);
}



document.addEventListener('DOMContentLoaded',function() {
	for (var key of Object.keys(defaultpicks)) {
		var val = localStorage.getItem("statselect_" + key);
		if (val != null) {
			showStats(key,val);
		}
		else {
			showStats(key,defaultpicks[key]);
		}


	}
})
