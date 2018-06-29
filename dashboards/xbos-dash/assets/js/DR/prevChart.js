var prevChart;
$(document).ready(function() {
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
			"renderTo": "prevChart",
			"type": 'column',
			"events": {
				"load": function(e) {
					$.ajax({
						"url": "http://127.0.0.1:5000/api/",
						"type": "GET",
						"dataType": "json",
						"success": function(d) {
							prevChart.hideLoading();
							prevChart.addSeries(processDD(d, "2018", true));
							prevChart.series[0].data[prevChart.series[0].data.length - 1].doDrilldown();
							$('#prevChartReset').addClass("scale-in");
							$('#goToAll').addClass("scale-in");
							$('#goToToday').addClass("scale-in");
						},
						"error": function(d) {
							prevChart.hideLoading();
							// prevChart.addSeries(processDD(d, "2018", true));
							// prevChart.series[0].data[prevChart.series[0].data.length - 1].doDrilldown();
						}
					});
				},
				"drilldown": function(e) {
					lev += 1;
					if (!e.seriesOptions) {
						prevChart.showLoading();
						$.ajax({
							"url": "http://127.0.0.1:5000/api/" + getPVE() + apis[lev],
							"type": "GET",
							"dataType": "json",
							"success": function(data) {
								prevChart.hideLoading();
								var dd = processDD(data, e.point.id);
								prevChart.userOptions.drilldown.series.push(dd);
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
					prevChart.setTitle({ "text": "Energy Usage" }, { "text": upSub(prevChart.subtitle.textStr) });
					prevChart.yAxis[0].setTitle({ "text": "kWh"});
					prevChart.options.chart.zoomType = "";
					$('#prevChartReset').hide();
					lev -= 1;
				}
			}
		},
		"title": {
			"text": 'Historical'
		},
		"subtitle": {
			// "text": "2018",
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

	prevChart = new Highcharts.Chart(options);
    prevChart.showLoading();

    $('#prevChartReset').click(function() {
        prevChart.xAxis[0].setExtremes(null, null);
    });
});
