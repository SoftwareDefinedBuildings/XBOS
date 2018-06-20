$(document).ready(function() {
	$.ajax({
		"url": "http://127.0.0.1:5000/api/hvac",
		"type": "GET",
		"dataType": "json",
		"success": function(d) {
			var ret = processResp(d);
			ret.forEach(function(v) { if (!v.length) { v[0] = "None"; }});
			$("#heatingDiv").html(ret[0].join(""));
			$("#coolingDiv").html(ret[1].join(""));
			$("#offDiv").html(ret[2].join(""));
		},
		"complete": function(d) {
			var zones = [];
			var hvacs = [];

			var i = 1;
			var z = $("#zone" + i);
			var h = $("#HVAC-" + i);
			while (i < 30) {
				z.css("opacity", .5);
				zones.push([z, i]);
				hvacs.push(h);
				i += 1;
				z = $("#zone" + i);
				h = $("#HVAC-" + i);
			}

			zones.forEach(function(v) {
				v[0].hover(function() {
					myHover(0);
					v[0].css("opacity", 1);
					hvacs[v[1] - 1].css("opacity", 1);
				}, function() {
					myHover(1);
					v[0].css("opacity", .5);
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
		var toRet = [[], [], []];
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
		toRet.push("<div class='zones' id='zone" + i + "'><div class='zoneNum'>Zone " + i + "</div><div class='zoneTemp'>" + t + "°</div></div>");
		return toRet;

	}
});
