var tempChart;
$(document).ready(function() {
    let c = ["#CC00FF", "#FF0099", "#00FFFF", "#00FF00", "#FF0000"]

    function getTime(et, x) { return toDate(et).toString().split(" ")[4].slice(0, x); }

    function toDate(et) {
        var d = new Date(0);
        d.setUTCSeconds(et);
        return d;
    }

    function clean(s, shorten=false, amt=null) {
        s = s.replace("-", "_");
        s = s.split("_");
        if (shorten && amt) {
            for (var i in s) {
                if (s[i].length > amt) {
                    s[i] = s[i].slice(0, amt);
                }
            }
        }
        for (var i in s) {
            s[i] = s[i].charAt(0).toUpperCase() + s[i].slice(1).toLowerCase();
        }
        s = s.join("");
        s = s.replace("Zone", "").replace("ZONE", "").replace("zone", "");
        s = s.replace("HVAC", "").replace("Hvac", "").replace("hvac", "");
        return s;
    }

    function processResp(j) {
        var toRet = [];
        var sums = [];
        var pa = [];
        var first = true;
        for (var z in j) {
            var toAdd = new Object();
            toAdd.name = clean(z);
            toAdd.id = toAdd.name;
            toAdd.data = makeData(j[z], toAdd.name, sums, first, pa);
            toRet.push(toAdd);
            if (first) { first = false; }
        }
        return select(sums, toRet, pa);
    }

    function select(sums, toRet, pa) {
        var zones = sums[0].length;
        if (zones > 5) {
            tempChart.setTitle(null, { text: "95% of data lies in gray area"});
            var avgs = [];
            var stds = [];
            // https://stackoverflow.com/questions/1295584/most-
            // efficient-way-to-create-a-zero-filled-javascript-
            // array#comment53285905_23326623
            var outs; (outs = []).length = zones; outs.fill(0);
            var times = sums.length;
            for (var l in sums) {
                var s = sums[l].reduce((pv, cv) => pv+cv, 0);
                var count = 0;
                for (var x in sums[l]) {
                    if (sums[l][x]) {
                        count += 1;
                    }
                }
                avgs.push(s/count);
                var diffs = [];
                for (var x in sums[l]) {
                    if (sums[l][x]) {
                        var dif = avgs[l] - sums[l][x];
                        diffs.push(dif * dif);
                    }
                }
                var diffsum = diffs.reduce((pv, cv) => pv+cv, 0);
                stds.push(Math.sqrt(diffsum / count));
                for (var x in sums[l]) {
                    if (sums[l][x] > (avgs[l] + 2*stds[l]) || sums[l][x] < (avgs[l] - 2*stds[l])) {
                        outs[x] += 1;
                    }
                }
            }
            var display = getMains(avgs, stds, pa);
            var i = 0;
            for (var x in toRet) {
                if (outs[x] / times > 0.05) {
                    if (i < c.length) {
                        toRet[x].color = c[i];
                        i += 1;
                    }
                } else {
                    toRet[x].visible = false;
                }
                display.push(toRet[x]);
            }
            return display;
        } else {
            return toRet;
        }
    }

    function getMains(m, s, pa) {
        var twoSD = s.map(function(x) { return x*2; });
        var upper = [];
        var lower = [];
        for (var i in m) {
            upper.push(m[i] + twoSD[i]);
            lower.push(m[i] - twoSD[i]);
        }

        var mean = new Object();
        mean.name = "Average";
        mean.data = stdData(m, pa, mean.name);
        mean.lineWidth = 1;
        mean.color = "#000000";
        // mean.showInLegend = false;

        var range = new Object();
        range.name = "Range"
        range.data = rangeData(lower, upper, pa, s);
        range.type = "arearange";
        range.linkedTo = ":previous";
        range.color = mean.color;
        range.lineWidth = 0;
        // range.zIndex = -1;
        // range.lineColor = "#7bd84e";
        range.fillOpacity = .2;
        range.marker = new Object();
        range.showInLegend = false;
        range.marker.enabled = false;

        return [mean, range];
    }

    function stdData(x, pa, n) {
        var toRet = [];
        for (var i in pa) {
            var toAdd = new Object();
            toAdd.name = pa[i];
            toAdd.y = round(x[i], 2);
            toAdd.id = n;
            // toAdd.id = n + " " + toAdd.name;
            toRet.push(toAdd);
        }
        return toRet;
    }

    function rangeData(l, u, pa, s) {
        toRet = [];
        for (var i in l) {
            var toAdd = new Object();
            toAdd.low = round(l[i], 2);
            toAdd.high = round(u[i], 2);
            toAdd.name = pa[i];
            toAdd.id = s[i];
            toRet.push(toAdd);
        }
        return toRet;
    }

    // function getMDY() {
    //     s = toDate(Date.now()/1000).toString();
    //     return s.slice(4, 10) + ", " + s.slice(11, 15);
    // }

    // http://www.jacklmoore.com/notes/rounding-in-javascript/
    function round(val, dec) { return Number(Math.round(val+'e'+dec)+'e-'+dec); }

    function makeData(j, z, sums, first, pa) {
        var toRet = [];
        var i = 0;
        for (var k in j) {
            var toAdd = new Object();
            toAdd.name = getTime(k/1000, 5);
            if (j[k]) {
                toAdd.y = round(j[k], 2);
            } else {
                toAdd.y = null;
            }
            if (first) {
                sums.push([toAdd.y]);
                pa.push(toAdd.name);
            } else {
                sums[i].push(toAdd.y);
            }
            toAdd.id = z + " " + toAdd.name;
            toRet.push(toAdd);
            i += 1;
        }
        return toRet;
    }

    function fixResp(d) {
        var ends = [];
        var last;
        for (var k in d) {
            for (var x in d[k]) {
                if (d[k][x] == "myNullVal" || d[k][x] == 0) {
                    d[k][x] = null;
                }
            }
            if (last) {
                if (x != last) {
                    console.log("ERROR");
                    return new Object();
                }
            }
            last = x;
            ends.push(d[k][x]);
        }
        var endNulls = true;
        for (var i in ends) {
            if (ends[i]) {
                endNulls = false;
                break;
            }
        }
        if (endNulls) {
            for (var k in d) {
                delete d[k][last];
            }
        }
        return d;
    }

    function pointFormatter() {
        if ("low" in this) {
            return "";
            // return '<span style="font-size:12px">σ=</span>' + round(this.id, 2) + '<br/>';
        // } else if (this.id == "Average") {
        //     return '<span style="font-size:12px">µ=</span>' + this.y+ '<br/>';
        } else {
            return '<span style="color:' + this.color + '; font-size:14px">●</span> <b>' + this.y+ '</b><br/>';
        }
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
            "renderTo": "tempChart",
            "events": {
                "load": function(e) {
                    $.ajax({
                        "url": "http://127.0.0.1:5000/api/hvac/day/30m",
                        "type": "GET",
                        "dataType": "json",
                        "success": function(d) {
                            tempChart.hideLoading();
                            d = fixResp(d);
                            var a = processResp(d);
                            for (var x in a) {
                                tempChart.addSeries(a[x], false);
                            }
                            // tempChart.setTitle(null, { text: getMDY()});
                            tempChart.redraw();
                            $('#tempChartReset').addClass("scale-in");
                        }
                    });
                }
            }
        },
        "title": {
            "text": "Today's Temperature"
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
            "pointFormatter": pointFormatter,
            "hideDelay": 500,
            "shared": true,
            "crosshairs": true,
            "padding": 6
        },
        "series": []
    };

    tempChart = new Highcharts.Chart(options);
    tempChart.showLoading();

    $('#tempChartReset').click(function() {
        tempChart.xAxis[0].setExtremes(null, null);
    });
});

