$(document).ready(function() {
	$("#hvac").hide();
	$("#hvac-loader").show();
	$("#hvac-loader").addClass("scale-in");
	$.ajax({
		"url": "http://127.0.0.1:5000/api/hvac",
		"type": "GET",
		"dataType": "json",
		"success": function(d) {
			$("#hvac-loader").addClass("scale-out");
			$("#hvac").addClass("scale-in");
			$("#hvac-loader").hide();
			$("#hvac").show();
			var ret = processResp(d);
			var bools = [];
			ret.forEach(function(v) {
				if (!v.length) {
					v[0] = "<span>None</span>";
					bools.push(false);
				} else {
					bools.push(true);
				}
			});
			var divs = [$("#heatingDiv"), $("#coolingDiv"), $("#offDiv"), $("#lightingDiv")];
			var instance = M.Collapsible.getInstance($("#hvac-dropdown"));
			setZones(ret, bools, divs, instance);
		},
		"complete": function(d) {
			var zones = [];
			var hvacs = [];

			var i = 1;
			var z = $("#zone" + i);
			var h = $("#HVAC-" + i);
			while (i < 30) {
				zones.push([z, i]);
				hvacs.push(h);
				i += 1;
				z = $("#zone" + i);
				h = $("#HVAC-" + i);
			}

			zones.forEach(function(v) {
				v[0].hover(function() {
					myHover(0);
					v[0].css("opacity", .5);
					hvacs[v[1] - 1].css("opacity", 1);
				}, function() {
					myHover(1);
					v[0].css("opacity", 1);
				});
			});

			function myHover(num) {
				hvacs.forEach(function(v) {
					v.css("opacity", num);
				});
			}
		}
	});

	function processResp(d) {
		var toRet = [[], [], [], []];
		var i = 1;
		for (var x in d) {
			var o = d[x];
			var r = makeHTML(o.cooling, o.heating, o.tstat_temperature, i);
			i += 1;
			toRet[r[0]].push(r[1]);
		}
		return toRet;
	}

	function makeHTML(c, h, t, i) {
		var toRet = [];
		if (h) {
			toRet.push(0);
		} else if (c) {
			toRet.push(1);
		} else {
			toRet.push(2);
		}
		toRet.push("<div class='zones' id='zone" + i + "'><span>Zone " + i + "</span><span>" + t + "°</span></div>");
		return toRet;

	}

	function setZones(r, b, d, i) {
		for (var x in r) {
			d[x].html(r[x].join(""));
			if (b[x]) {
				i.open(x);
			}
		}
	}
});
