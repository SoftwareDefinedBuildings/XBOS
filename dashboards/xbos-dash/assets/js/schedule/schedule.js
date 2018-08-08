$(document).ready(function() {
	var s = document.getElementById("slider");
	var monopts = {
		start: [0, 8, 18, 24],
		connect: [true, true, true, true, true],
		range: { 'min': 0, 'max': 24 }
	}
	noUiSlider.create(s, monopts);
	monlist = s.noUiSlider.get();
	$("#mon-add").click(function() {
		monlist = s.noUiSlider.get().map(
			function(item) {
				return parseFloat(item);
			}
		);
		monlist = $.merge([0], monlist);
		console.log(monlist);
		s.noUiSlider.destroy();
		monopts.start = monlist;
		noUiSlider.create(s, monopts);
		console.log(monopts);
	});
	
});
