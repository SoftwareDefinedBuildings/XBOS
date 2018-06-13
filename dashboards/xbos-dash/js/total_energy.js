var energyChart;
$(document).ready(function() {
	let apis = ["all", "year/in/month", "month/in/1d", "day/in/10m"];
	let levels = ["years", "months", "days", "hours"];
	// // assert(apis.length == levels.length);
	let myLev = 1; // change to 0 if we have data for multiple years
	var lev = myLev;

	// date format example: Fri Jun 01 2018 17:15:33 GMT-0700 (Pacific Daylight Time)
	function getName(s) {
		switch(lev) {
			case 0: //year
				return s[3];
			case 1: //month
				return s[1];
			case 2: //day
				return s[2];
			case 3:
				return s[4].slice(0, 5);
		}
	}

	function toDate(et) {
		var d = new Date(0);
		d.setUTCSeconds(et);
		return d;
	}

	function getDDID(s) {
		switch(lev) {
			case 0:
				return s[3];
			case 1:
				return s[1] + " " + s[3];
			case 2:
				return s[1] + " " + s[2] + ", " + s[3];
			case 3:
				return s[1] + " " + s[2] + ", " + s[3] + " " + s[4].slice(0, 5);
		}
	}

	function processResp(j) {
		j = getData(j);
		var toRet = makeData(j);
		toRet.reverse(); // might not need reverse
		addDrill(toRet); // won't be needed if accessing all data
		return toRet;
	}

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
			toAdd.y = j[k];
			// toAdd.drilldown = toAdd.id;
			toRet.push(toAdd);
		}
		return toRet;
	}

	function processDD(j, e) {
		j = getData(j);
		var toRet = new Object();
		toRet.name = e;
		toRet.id = toRet.name;
		energyChart.setTitle(null, { text: toRet.name});
		if (end()) {
			energyChart.setTitle({ "text": "Power Consumption" }, null);
			energyChart.yAxis[0].setTitle({ "text": "kW"});
			energyChart.options.chart.zoomType = "x";
			$('#energyChartReset').show();
		}
		toRet.data = makeData(j);
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

	function getPVE() {
		if (end()) {
			return "power/";
		} else {
			return "energy/";
		}
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
			"renderTo": "chart-total-energy",
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
							energyChart.series[0].setData(processResp(d));
							// energyChart.series[0].data[energyChart.series[0].data.length - 1].doDrilldown();
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
								energyChart.addSeriesAsDrilldown(e.point, processDD(data, e.point.id));
							}
						});
					} else {
						console.log("already have it");
					}
				},
				"drillup": function(e) {
					energyChart.setTitle(null, { "text": upSub(energyChart.subtitle.textStr) });
					energyChart.yAxis[0].setTitle({ "text": "kWh"});
					energyChart.setTitle({ "text": "Energy Usage" }, null);
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
			"showDuration": 1000,
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
				"animation": true
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
			"pointFormat": '<span style="color:{point.color}">{point.name}</span>: <b>{point.y:.2f}</b> <br/>',
			"hideDelay": 1000
		},
		"series": [
			{
				"name": "2018",
				"id": "2018",
				"data": []
			}
		],
		"drilldown": {
			"drillUpButton": {
				"position": {
					"verticalAlign": "top",
					"align": "right",
					"y": -50,
					"x": -40
				}
			},
			"series": [
				{
					"name": "Mar 2018",
					"id": "Mar 2018",
					"data": [
						{
							"name": "ideeekk",
							"y": 6
						}
					]
				}
			]
		}
	};

	energyChart = new Highcharts.Chart(options);

	$('#energyChartReset').click(function() {
		energyChart.xAxis[0].setExtremes(null, null);
    });
    $('#energyChartReset').hide();
});
