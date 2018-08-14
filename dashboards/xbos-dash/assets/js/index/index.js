$(document).ready(function() {
	M.AutoInit();
	var elem = document.querySelector('.collapsible.expandable');
	var instance = M.Collapsible.init(elem, {
		accordion: false
	});
});
