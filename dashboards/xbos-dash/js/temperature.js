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
        if (zones > 6) {
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
                if (outs[x] > 0) {
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
        mean.lineWidth = 5;
        mean.color = "#888888";

        var range = new Object();
        range.name = "Range"
        range.data = rangeData(lower, upper, pa, range.name);
        range.type = "arearange";
        range.lineWidth = 0;
        range.linkedTo = ":previous";
        range.color = mean.color;
        range.fillOpacity = .7;
        range.zIndex = -1;
        range.marker = new Object();
        range.marker.enabled = false;

        return [mean, range];
    }

    function stdData(x, pa, n) {
        var toRet = [];
        for (var i in pa) {
            var toAdd = new Object();
            toAdd.name = pa[i];
            toAdd.y = round(x[i], 2);
            toAdd.id = n + " " + toAdd.name;
            toRet.push(toAdd);
        }
        return toRet;
    }

    function rangeData(l, u, pa, n) {
        toRet = [];
        for (var i in l) {
            var toAdd = new Object();
            toAdd.low = round(l[i], 2);
            toAdd.high = round(u[i], 2);
            toAdd.name = pa[i];
            toAdd.id = n + " " + toAdd.name;
            toRet.push(toAdd);
        }
        return toRet;
    }

    function getMDY() {
        s = toDate(Date.now()/1000).toString();
        return s.slice(4, 10) + ", " + s.slice(11, 16);
    }

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

    var options = {
        "chart": {
            "renderTo": "chart-temperature",
            "events": {
                "load": function(e) {
                    this.showLoading();
                    $.ajax({
                        "url": "http://127.0.0.1:5000/api/hvac/day/30m", //"url": "http://127.0.0.1:5000/api/energy/year/in/month", 
                        "type": "GET",
                        "dataType": "json",
                        "success": function(d) {
                            tempChart.hideLoading();
                            d = fixResp(d);
                            var a = processResp(d);
                            for (var x in a) {
                                tempChart.addSeries(a[x], false);
                            }
                            tempChart.setTitle(null, { text: "Today: " + getMDY()});
                            tempChart.redraw();
                        }
                    });
                }
            }
        },
        "title": {
            "text": 'Temperature'
        },
        "subtitle": {
            "text": "",
            "style": {
                "fontSize": 16
            }
        },
        "loading": {
            "hideDuration": 0,
            "showDuration": 1000,
            "style": {
                "opacity": .75
            }
        },
        "xAxis": {
            "type": "category",
            "tickInterval": 8
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
            "verticalAlign": "middle"
        },
        "plotOptions": {
            "line": {
                "marker": {
                    "enabled": false
                }
            },
            "series": {
                "animation": true,
                "point": {
                    "events": {
                        // http://jsfiddle.net/gh/get/library/pure/highcharts/
                        // highcharts/tree/master/samples/highcharts/plotoptions/
                        // series-point-events-mouseover/
                        "mouseOver": function () {
                            var myLabel = this.series.chart;
                            if (!myLabel.lbl) {
                                myLabel.lbl = myLabel.renderer.label('').attr(
                                    {
                                        padding: 0,
                                        r: 10,
                                        fill: "#000000"
                                    }
                                ).css(
                                    {
                                        color: '#FFFFFF'
                                    }
                                ).add();
                            }
                            myLabel.lbl.attr(
                                {
                                    text: this.id + " " + this.y
                                }
                            );
                        }
                        // },
                        // "mouseOut": function () {
                        //     if (this.series.chart.lbl) {
                        //         this.series.chart.lbl.hide();
                        //     }
                        // }
                    }
                }
            }
        },
        "tooltip": {
            "enabled": false,
            // "headerFormat": '<span style="font-size:12px">{series.name}</span><br>',
            // "pointFormat": '<span style="color:{point.color}">{point.name}</span> {point.y}</b> <br/>',
            // "hideDelay": 1000
        },
        "series": []
    };

    tempChart = new Highcharts.Chart(options);
});
