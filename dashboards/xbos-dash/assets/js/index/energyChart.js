var energyChart;
$(document).ready(function() {
	let apis = ["all", "year/in/month", "month/in/1d", "day/in/10m"];
	let levels = ["years", "months", "days", "hours"];
	// // assert(apis.length == levels.length);
	let myLev = 1; // change to 0 if we have data for multiple years
	var lev = myLev;
	var onload = true;

	// date format example: Fri Jun 01 2018 17:15:33 GMT-0700 (Pacific Daylight Time)
	function getName(s) {
		switch(lev) {
			case 0: //year
				return s[3];
			case 1: //month
				return s[1];
			case 2: //day
				return s[2];
			case 3: //time (HH:MM)
				return s[4].slice(0, 5);
		}
	}

	function toDate(et) {
		var d = new Date(0);
		d.setUTCSeconds(et);
		// TODO: modify timezone
		return d;
	}

	function getDDID(s) {
		switch(lev) {
			case 0: //year
				return s[3];
			case 1: //month year
				return s[1] + " " + s[3];
			case 2: //month day, year
				return s[1] + " " + s[2] + ", " + s[3];
			case 3: //month day, year time (HH:MM)
				return s[1] + " " + s[2] + ", " + s[3] + " " + s[4].slice(0, 5);
		}
	}

	// function processResp(j) {
	// 	j = getData(j);
	// 	var toRet = makeData(j);
	// 	var x = true;
	// 	if (x) {
	// 		toRet.reverse(); // might not need reverse
	// 		x = false;
	// 	}
	// 	addDrill(toRet); // won't be needed if accessing all data
	// 	return toRet;
	// }

	function getData(j) {
		if ("0" in j) { return j["0"]; }
		if ("readings" in j) { return j["readings"]; }
		for (var k in j) {
			if (j[k] == "myNullVal") {
				j[k] = null;
			}
		}
		return j;
	}

	function addDrill(x) {
		if (!end()) {
			x[x.length - 1].drilldown = x[x.length - 1].id;
		}
	}

	function makeData(j) {
		var toRet = [];
		for (var k in j) {
			var toAdd = new Object();
			var date = toDate(k/1000).toString().split(" ");
			toAdd.name = getName(date);
			toAdd.id = getDDID(date);
			toAdd.y = round(j[k], 2);
			// if (!end()) {
			// 	toAdd.drilldown = toAdd.id;
			// }
			toRet.push(toAdd);
		}
		return toRet;
	}

	// http://www.jacklmoore.com/notes/rounding-in-javascript/
	function round(val, dec) { return Number(Math.round(val+'e'+dec)+'e-'+dec); }

	function processDD(j, e, flip=false) {
		j = getData(j);
		var toRet = new Object();
		toRet.name = e;
		toRet.id = toRet.name;
		toRet.data = makeData(j);
		if (flip) {
			toRet.data.reverse();
		}
		addDrill(toRet.data);
		toRet.type = getType();
		return toRet;
	}

	function end() { return lev == (levels.length - 1); }

	function getType() {
		if (!end()) {
			return "column";
		} else {
			return "line";
		}
	}

	function upSub(id) {
		id = id.replace(",", "");
		id = id.split(" ");
		switch(lev) {
			case 1: 
				return "All";
			case 2: //date format example: Jun 2018
				return "2018";
				// return id[1];
			case 3: //date format example: Jun 01, 2018
				return id[0] + " " + id[2];
		}
	}

	function drill(e) {
		if (end()) {
			energyChart.setTitle({ "text": "Power Consumption" }, {text: e});
			energyChart.yAxis[0].setTitle({ "text": "kW"});
			energyChart.options.chart.zoomType = "x";
			$('#energyChartReset').show();
		} else {
			energyChart.setTitle(null, { text: e});
		}
	}

	function getPVE() {
		if (end()) {
			return "power/";
		} else {
			return "energy/";
		}
	}

	function goDown(dd) {
		energyChart.addSeries(dd, false);
		energyChart.series[0].data[energyChart.series[0].data.length - 1].doDrilldown();
		energyChart.series[energyChart.series.length - 1].remove();
	}

	var options = {
		"chart": {
			"resetZoomButton": {
				"theme": {
					"display": "none"
				}
			},
			"scrollablePlotArea": {
				"minWidth": 450
			},
			"renderTo": "energyChart",
			"type": 'column',
			"events": {
				"load": function(e) {
					this.showLoading();
					$.ajax({
						"url": "http://127.0.0.1:5000/api/" + getPVE() + apis[lev],
						"type": "GET",
						"dataType": "json",
						"success": function(d) {
							energyChart.hideLoading();
							energyChart.addSeries(processDD(d, "2018", true));
							energyChart.series[0].data[energyChart.series[0].data.length - 1].doDrilldown();
							$('#energyChartReset').show();
							$('#goToAll').show();
							$('#goToToday').show();
						}
					});
				},
				"drilldown": function(e) {
					lev += 1;
					if (!e.seriesOptions) {
						energyChart.showLoading();
						$.ajax({
							"url": "http://127.0.0.1:5000/api/" + getPVE() + apis[lev],
							"type": "GET",
							"dataType": "json",
							"success": function(data) {
								energyChart.hideLoading();
								var dd = processDD(data, e.point.id);
								energyChart.userOptions.drilldown.series.push(dd);
								lev -= 1;
								e.point.doDrilldown();
								if (onload && !end()) {
									goDown(dd);
								} else {
									onload = false;
								}
								return;
							}
						});
					} else {
						drill(e.point.id);
					}
				},
				"drillup": function(e) {
					energyChart.setTitle({ "text": "Energy Usage" }, { "text": upSub(energyChart.subtitle.textStr) });
					energyChart.yAxis[0].setTitle({ "text": "kWh"});
					energyChart.options.chart.zoomType = "";
					$('#energyChartReset').hide();
					lev -= 1;
				}
			}
		},
		"title": {
			"text": 'Energy Usage'
		},
		"subtitle": {
			"text": "2018",
			"style": {
				"fontSize": 18
			}
		},
		"loading": {
			"hideDuration": 0,
			"showDuration": 0,
			"style": {
				"opacity": .75
			}
		},
		"lang": {
			"drillUpText": "◄ {series.name}"
		},
		"xAxis": {
			"type": "category"
		},
		"yAxis": {
			"title": {
				"text": "kWh"
			}
		},
		"plotOptions": {
			"series": {
				"animation": true,
				"stickyTracking": true,
				"states": {
					"hover": {
						"enabled": false
					}
				}
			},
			"line": {
				"marker": {
					"enabled": false
				}
			}
		},
		"credits": {
			"enabled": false
		},
		"legend": {
			"enabled": false
		},
		"tooltip": {
			"headerFormat": '<span style="font-size:11px">{point.name}</span><br>',
			"pointFormat": '<span style="color:{point.color}">{point.name}: </span><b>{point.y:.2f}</b><br/>',
			"hideDelay": 500,
			"crosshairs": true,
			"padding": 6
		},
		"series": [],
		"drilldown": {
			"drillUpButton": {
				"position": {
					"verticalAlign": "top",
					"align": "right",
					"y": -50,
					"x": -40
				}
			},
			"series": []
		}
	};

	energyChart = new Highcharts.Chart(options);

	function resetAxes() {
		energyChart.xAxis[0].setExtremes(null, null);
	}

	function showAll() {
		while (lev != myLev) {
			energyChart.drillUp();
		}
	}

	$('#energyChartReset').click(resetAxes);

	$('#goToAll').click(showAll);

	$('#goToToday').click(function() {
		var s = toDate(Date.now()/1000).toString();
        s = s.slice(4, 10) + ", " + s.slice(11, 15);
		if (energyChart.subtitle.textStr != s) {
			showAll();
			while (!end()) {
				energyChart.series[0].data[energyChart.series[0].data.length - 1].doDrilldown();
			}
		}
	});

	$('#energyChartReset').hide();
	$('#goToAll').hide();
	$('#goToToday').hide();

});
