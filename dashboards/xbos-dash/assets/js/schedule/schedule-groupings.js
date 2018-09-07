$(document).ready(function() {
	let numz = 9;
	var i = 0;
	while (i < numz) {
		$("#container").append("<div class='row valign-wrapper center-align sel-col'></div>");
		i += 1;
	}

	var numg = 9;
	var x;
	$(".sel-col").each(function(i) {
		i += 1;
		x = 0;
		$(this).append("<div style='margin-left: 0;' class='col s2-7'><h6>Zone " + i + "</h6></div>");
		while (x < numg) {
			$(this).append("<div class='col tiny-2'><label><input class='with-gap' name='group" + i + "' type='radio' /><span></span></label></div>");
			x += 1;
		}
	});

	$("#add-group").click(function() {
		numg += 1;
		if (numg > 17) { numg = 17; return; }
		$(".sel-col").each(function(i) {
			i += 1;
			$(this).append("<div class='col tiny-2'><label><input class='with-gap' name='group" + i + "' type='radio' /><span></span></label></div>");
		});
	});


	$("#del-group").click(function() {
		numg -=1;
		if (numg < 1) { numg = 1; return; }
		$(".sel-col").each(function() {
			// https://stackoverflow.com/questions/30492918/
			$(this).children().last().remove();
		});
	});
});
