var DRChart;
$(document).ready(function() {
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
            "renderTo": "DRChart",
            "events": {
                "load": function(e) {
                    $.ajax({
                        "url": "http://127.0.0.1:5000/api/hvac/day/30m",
                        "type": "GET",
                        "dataType": "json",
                        "success": function(d) {
                            DRChart.hideLoading();
                            d = fixResp(d);
                            var a = processResp(d);
                            for (var x in a) {
                                DRChart.addSeries(a[x], false);
                            }
                            // DRChart.setTitle(null, { text: getMDY()});
                            DRChart.redraw();
                            $('#DRChartReset').addClass("scale-in");
                        },
                        "error": function(d) {
                            DRChart.hideLoading();
                            // d = fixResp(d);
                            // var a = processResp(d);
                            // for (var x in a) {
                                // DRChart.addSeries(a[x], false);
                            // }
                            // DRChart.setTitle(null, { text: getMDY()});
                            // DRChart.redraw();
                            $('#DRChartReset').addClass("scale-in");
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
                "fontSize": 12
            }
        },
        "loading": {
            "hideDuration": 0,
            "showDuration": 0,
            "style": {
                "opacity": .75
            }
        },
        "xAxis": {
            "type": "category"
        },
        "yAxis": {
            "title": {
                "text": "°F"
            }
        },
        "credits": {
            "enabled": false
        },
        "legend": {
            "enabled": true,
            "layout": "vertical",
            "align": "right",
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
                }
            }
        },
        "tooltip": {
            "headerFormat": '<span style="font-size:14px">{point.key}</span><br/>',
            // "pointFormatter": pointFormatter,
            "hideDelay": 500,
            "shared": true,
            "crosshairs": true,
            "padding": 6
        },
        "series": []
    };

    DRChart = new Highcharts.Chart(options);
    DRChart.showLoading();

    $('#DRChartReset').click(function() {
        DRChart.xAxis[0].setExtremes(null, null);
    });
});

