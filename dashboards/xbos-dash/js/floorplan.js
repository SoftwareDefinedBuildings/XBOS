$(document).ready(function() {
	let numZones = 5;
	var zones = [];
	var hvacs = [];

	var i = 1;
	while (i <= numZones) {
		var z = $("#zone" + i);
		z.css("opacity", .6);
		zones.push([z, i]);
		hvacs.push($("#HVAC-" + i));
		i += 1;
	}

	zones.forEach(function(v) {
		v[0].hover(function() {
			myHover(0);
			v[0].css("opacity", 1);
			$("#HVAC-" + v[1]).css("opacity", 1);
		}, function() {
			myHover(1);
			v[0].css("opacity", .6);
		});
	});

	function myHover(num) {
		hvacs.forEach(function(v) {
			v.css("opacity", num);
		});
	}
});