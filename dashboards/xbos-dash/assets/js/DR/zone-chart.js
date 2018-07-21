var zoneChart;
$(document).ready(function() {
	let lines = ["Solid", "LongDash", "Dash", "ShortDashDot", "DashDot", "ShortDash", "Dot", "ShortDot"];
	let c = ["#000000", "#000080", "#800000", "#e6194b", "#008080", "#911eb4", "#0082c8"];

	function getTime(et, x) { return toDate(et).toString().split(" ")[4].slice(0, x); }

	function toDate(et) {
		var d = new Date(0);
		d.setUTCSeconds(et);
		return d;
	}

	// http://www.jacklmoore.com/notes/rounding-in-javascript/
	function round(val, dec) { return Number(Math.round(val+'e'+dec)+'e-'+dec); }

	function processResp(j) {
		var toRet = [];
		for (var z in j) {
			var lst = [];
			var prevKeys = [];
			var st;
			var low = 500;
			var up = -500;
			for (var s in j[z]) {
				var toAdd = new Object();
				toAdd.id = clean(z).toLowerCase() + " " + s;
				toAdd.name = toAdd.id;
				if (s == "state") {
					toAdd.data = j[z][s];
					// toAdd.data = makeState(j[z][s], prevKeys, toAdd.id);
					st = toAdd;
					// lst.push(toAdd);
				} else {
					var ret = makeData(j[z][s], toAdd.id);
					toAdd.data = ret[0];
					var k = ret[1];
					if (k.length > prevKeys.length) { prevKeys = k; }
					if (ret[2] < low) { low = ret[2]; }
					if (ret[3] > up) { up = ret[3]; }
					lst.push(toAdd);
				}
			}
			st.data = makeState(st.data, prevKeys, st.id, low, up);
			st.lineWidth = 4;
			st.yAxis = 1;
			st.color = "#000000";
			lst.push(st);
			for (var i = 1; i < lst.length; i += 1) { lst[i].linkedTo = clean(z);
				// lst[i].dashStyle = lines[i];
			}
			lst[0].dashStyle = lines[0];
			lst[0].name = clean(z);
			lst[0].id = lst[0].name;
			if (!toRet.length) { lst[0].visible = true; }
			else { lst[0].visible = false; }
			$.merge(toRet, lst);
		}
		console.log(toRet);
		return toRet;
	}

	function makeState(j, l, n, low, up) {
		var toRet = [];
		var prev = null;
		var r;
		for (var k in l) {
			var toAdd = new Object();
			toAdd.name = getTime(l[k]/1000, 5);
			toAdd.id = n + " " + toAdd.name;
			if (l[k] in j) {
				r = stateClean(j[l[k]], low, up); 
				prev = round(r[0], 2);
			}
			toAdd.y = prev;
			toAdd.id += " " + r[1];
			toRet.push(toAdd);
		}
		return toRet;
	}

	function stateClean(x, low, up) {
		// low -= 3;
		// up += 3;
		// if (x == "off") { return [(low+up) / 2, "off"]; }
		// if (x == "heat stage 1") { return [((low+up)/2 + up)/2, "he1"]; }
		// if (x == "heat stage 2") { return [up, "he2"]; }
		// if (x == "cool stage 1") { return [((low+up)/2 + low)/2, "co1"]; }
		// if (x == "cool stage 2") { return [low, "co2"]; }
		// console.log("strange");
		if (x == "off") { return [-2, "off"]; }
		if (x == "heat stage 1") { return [2, "he1"]; }
		if (x == "heat stage 2") { return [0, "he2"]; }
		if (x == "cool stage 1") { return [0, "co1"]; }
		if (x == "cool stage 2") { return [0, "co2"]; }
	}

	function makeData(j, n) {
		var toRet = [];
		var ret = [];
		var min = 500;
		var max = -500;
		for (var k in j) {
			ret.push(k);
			var toAdd = new Object();
			toAdd.name = getTime(k/1000, 5);
			toAdd.id = n + " " + toAdd.name;
			toAdd.y = round(j[k], 2);
			if (toAdd.y < min) { min = toAdd.y; }
			if (toAdd.y > max) { max = toAdd.y; }
			toRet.push(toAdd);
		}
		// console.log(min, max);
		return [toRet, ret, min, max];
	}

	function clean(s, shorten=false, amt=null) {
		s = s.replace("-", "_");
		s = s.split("_");
		if (shorten && amt) { for (var i in s) { if (s[i].length > amt) { s[i] = s[i].slice(0, amt); }}}
		for (var i in s) { s[i] = s[i].charAt(0).toUpperCase() + s[i].slice(1).toLowerCase(); }
		s = s.join("");
		s = s.replace("Zone", "").replace("ZONE", "").replace("zone", "");
		s = s.replace("HVAC", "").replace("Hvac", "").replace("hvac", "");
		return s;
	}

	function pointFormatter() {
		// if ("state" in this) {
			// last 3 chars
			// return this.id.toString().reverse().slice(3).reverse();
		// }
		// if (state in $(this).id) { return "sdf"; }
		// else { 
			return "<span style='font-size: 14px;'>" + this.id.split(" ")[1] + this.y + "<br/>";
		// }
    }

	var options = {
		"chart": {
			"resetZoomButton": {
				"theme": {
					"display": "none"
				}
			},
			"zoomType": "x",
			"scrollablePlotArea": {
				"minWidth": 450
			},
			"renderTo": "zone-DR",
			"events": {
				"load": function(e) {
					$.ajax({
						"url": "http://127.0.0.1:5000/api/hvac/day/30m",
						"type": "GET",
						"dataType": "json",
						"success": function(d) {
							zoneChart.hideLoading();
							d = fixResp(d);
							var a = processResp(d);
							for (var x in a) {
								zoneChart.addSeries(a[x], false);
							}
							// zoneChart.setTitle(null, { text: getMDY()});
							zoneChart.redraw();
						},
						"error": function(d) {
							var d = {"EastZone": { "inside": { "1520322778000": 30, "1520326378000": 69.204815864, "1520329978000": 69.2362606232, "1520333578000": 69.2615819209, "1520337178000": 69.2750708215, "1520340778000": 69.2776203966, "1520344378000": 69.2759206799, "1520347978000": 69.5719546742, "1520351578000": 69.2436260623, "1520355178000": 69.6504249292, "1520358778000": 70.0016997167, "1520362378000": 70.3898550725, "1520365978000": 70.4116147309, "1520369578000": 70.6051136364, "1520373178000": 70.728125, "1520376778000": 70.856980057, "1520380378000": 71.547592068, "1520383978000": 72.1147727273 }, "outside": { "1520322778000": 89.49, "1520326378000": 89.2, "1520329978000": 89.22, "1520333578000": 89.29, "1520337178000": 89.25, "1520340778000": 89.26, "1520344378000": 89.29, "1520347978000": 89.52, "1520351578000": 89.23, "1520355178000": 89.62, "1520358778000": 80.07, "1520362378000": 80.35, "1520365978000": 80.49, "1520369578000": 80.64, "1520373178000": 80.7, "1520376778000": 80.8, "1520380378000": 81.5, "1520383978000": 82.13 }, "heating_setpoint": { "1520322778000": 50, "1520326378000": 50, "1520329978000": 50, "1520333578000": 50, "1520337178000": 50, "1520340778000": 50, "1520344378000": 50, "1520347978000": 50, "1520351578000": 50, "1520355178000": 50, "1520358778000": 70, "1520362378000": 70, "1520365978000": 70, "1520369578000": 70, "1520373178000": 70, "1520376778000": 70, "1520380378000": 70, "1520383978000": 70 }, "cooling_setpoint": { "1520322778000": 80, "1520326378000": 80, "1520329978000": 80, "1520333578000": 80, "1520337178000": 80, "1520340778000": 80, "1520344378000": 80, "1520347978000": 80, "1520351578000": 80, "1520355178000": 80, "1520358778000": 74, "1520362378000": 74, "1520365978000": 74, "1520369578000": 74, "1520373178000": 74, "1520376778000": 74, "1520380378000": 74, "1520383978000": 74 }, "state": { "1520322778000": "heat stage 1", "1520329978000": "off", "1520358778000": "heat stage 1", "1520365978000": "heat stage 2", "1520369578000": "off", "1520373178000": "heat stage 1" }}, "NorthZone": {"inside": { "1520322778000": 64, "1520326378000": 64, "1520329978000": 64, "1520333578000": 64, "1520337178000": 64, "1520340778000": 64, "1520344378000": 64, "1520347978000": 64, "1520351578000": 64, "1520355178000": 64, "1520358778000": 74, "1520362378000": 74, "1520365978000": 74, "1520369578000": 74, "1520373178000": 74, "1520376778000": 74, "1520380378000": 74, "1520383978000": 74}, "outside": { "1520322778000": 95, "1520326378000": 95, "1520329978000": 95, "1520333578000": 95, "1520337178000": 95, "1520340778000": 95, "1520344378000": 95, "1520347978000": 95, "1520351578000": 95, "1520355178000": 95, "1520358778000": 83, "1520362378000": 83, "1520365978000": 83, "1520369578000": 83, "1520373178000": 84, "1520376778000": 84, "1520380378000": 84, "1520383978000": 84}, "heating_setpoint": { "1520322778000": 51, "1520326378000": 51, "1520329978000": 51, "1520333578000": 51, "1520337178000": 51, "1520340778000": 51, "1520344378000": 51, "1520347978000": 51, "1520351578000": 51, "1520355178000": 51, "1520358778000": 75, "1520362378000": 75, "1520365978000": 75, "1520369578000": 75, "1520373178000": 75, "1520376778000": 75, "1520380378000": 75, "1520383978000": 75}, "cooling_setpoint": { "1520322778000": 81, "1520326378000": 81, "1520329978000": 81, "1520333578000": 81, "1520337178000": 81, "1520340778000": 81, "1520344378000": 81, "1520347978000": 81, "1520351578000": 81, "1520355178000": 81, "1520358778000": 75, "1520362378000": 75, "1520365978000": 75, "1520369578000": 75, "1520373178000": 75, "1520376778000": 75, "1520380378000": 75, "1520383978000": 75}, "state": { "1520322778000": "heat stage 2", "1520329978000": "off", "1520358778000": "heat stage 2", "1520365978000": "heat stage 1", "1520369578000": "off", "1520373178000": "heat stage 2"}}};
							var a = processResp(d);

							zoneChart.addSeries(a[0], false);
							zoneChart.setTitle(null, { text: "Zone: " + zoneChart.series[0].name });
							zoneChart.series[0].color = c[0];
							var flag = false;
							var mod = 1;
							var p;
							for (var x = 1; x < a.length; x += 1) {
								zoneChart.addSeries(a[x], false);
								if (!flag && a[x].linkedTo) {
									zoneChart.series[x].color = c[x];
									mod += 1;
								} else {
									flag = true;
									p = x % mod;
									zoneChart.series[x].color = c[p];
								}
							}
							zoneChart.hideLoading();
							zoneChart.redraw();
						}
					});
				}
			}
		},
		"title": {
			"text": "Simulated"
		},
		"subtitle": {
			"text": "",
			"style": {
				"fontSize": 16
			}
		},
		"loading": {
			"hideDuration": 0,
			"showDuration": 0,
			"style": {
				"opacity": .75
			}
		},
		"xAxis": [
			{
				"id": "myXAxis",
				"type": "category",
				"plotBands": {
					"color": "#eeeeee",
					"from": 2,
					"to": 6
				}
			}
		],
		"yAxis": [
			{
				"title": { "text": "°F" },
				"height": 225
			},
			{
				"title": { "text": "State" },
				"height": 50,
				"top": 310
			}
		],
		"credits": {
			"enabled": false
		},
		"legend": {
			"enabled": true,
			"layout": "vertical",
			"align": "left",
			"verticalAlign": "middle",
			"maxHeight": 400
		},
		"plotOptions": {
			"line": {
				"marker": {
					"enabled": false,
				}
			},
			"series": {
				"stickyTracking": true,
				"states": {
					"hover": {
						"enabled": false
					}
				},
				"events": {
					"legendItemClick": function () {
						var s = this.chart.series;
						for (var i = 0; i < s.length; i += 1) {
							s[i].hide();
						}
						zoneChart.setTitle(null, { text: "Zone: " + this.name} );
						return true;
					}
				}
			}
		},
		"tooltip": {
			"headerFormat": '<span style="font-size:14px">{point.key}</span><br/>',
			"pointFormatter": pointFormatter,
			"hideDelay": 500,
			"shared": true,
			"crosshairs": true,
			"padding": 6
		},
		"series": []
	};

	zoneChart = new Highcharts.Chart(options);
	zoneChart.showLoading();

	$('#zone-reset').click(function() { zoneChart.xAxis[0].setExtremes(null, null); });
});

