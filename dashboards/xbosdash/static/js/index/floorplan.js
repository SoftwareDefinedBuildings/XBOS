$(document).ready(function() {

    $.ajax({
        // make sure file exists. replace 'ciee' with name of building (underscores)
        url: '/svg/ciee.svg',
        success: function(data) {
            console.log(data);
            $("#floorplan").html(data)
        }
    });

	$("#hvac").hide();
	$("#hvac-loader").show();
	$("#hvac-loader").addClass("scale-in");
	var setpts = [[]];
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
			console.log(setpts);
			var bools = [];
			ret.forEach(function(v) {
				if (!v.length) {
					v[0] = "None";
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
			// TODO: fix this
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
					v[0].find('span').each(function() { $(this).css("opacity", .5); });
					hvacs[v[1] - 1].css("opacity", 1);
				}, function() {
					myHover(1);
					v[0].find('span').each(function() { $(this).css("opacity", 1); });
				});
			});

			function myHover(num) { hvacs.forEach(function(v) { v.css("opacity", num); });}
		}
	});
	
	var tb = true;
	$("#tempbtn").click(function() {
		var x = $(this);
		var ret = [];
		var v; var zt; var change;
		if (tb) {
			y = "save";
			$(".zonestemp").each(function() {
				$(this).replaceWith("<div id='" + this.id + "' class='right-align col s5 zonestemp'><input class='my-input' type='number' max=90 min=35 value='" + $(this).html().replace("°", "") + "' /></div>");
			});
		} else {
			y = "edit";
			$(".zonestemp").each(function() {
				v = myclean($(this).find("input").prop("value"));
				zt = parseInt(this.id.replace("zt", ""));
				change = getChange(v, zt);
				ret.push({id: this.id.replace("zt", ""), val: v, setpoint: change});
				$(this).replaceWith("<span id='" + this.id + "' class='col s5 zonestemp right-align'>" + v + "°</span>");
			});
		}
		x.removeClass("scale-in");
		x.addClass("scale-out");
		setTimeout(function() {
			x.html("<i id='tempicon' class='material-icons right'>" + y + "</i>" + y);
			x.removeClass("scale-out");
			x.addClass("scale-in");
			clearTimeout(this);
		}, 250);
		if (!tb) { console.log(ret); M.toast({html: "Your preferences have been applied.", displayLength: 3000}); }
		tb = !tb;
	});

	function getChange(v, zt) {
		var sp = setpts[zt];
		if (Math.abs(v - sp[0]) < Math.abs(v - sp[1])) { return "heating"; } else { return "cooling"; }
	}

	function myclean(x) {
		x = Math.floor(x);
		if (x < 35) { return 35; }
		if (x > 90) { return 90; }
		return x;
	}

	function processResp(d) {
		var toRet = [[], [], [], []];
		var i = 1;
		for (var x in d) {
			var o = d[x];
			setpts.push([o.heating_setpoint, o.cooling_setpoint]);
			var r = makeHTML(o.cooling, o.heating, o.tstat_temperature, i);
			i += 1;
			toRet[r[0]].push(r[1]);
		}
		return toRet;
	}

	function makeHTML(c, h, t, i) {
		var toRet = [];
		if (h) { toRet.push(0); }
		else if (c) { toRet.push(1); }
		else { toRet.push(2); }
		toRet.push("<div class='row zones valign-wrapper' id='zone" + i + "'><span class='col s7 left-align'>Zone " + i + "</span><span id='zt" + i + "' class='col s5 zonestemp right-align'>" + myclean(t.toString()) + "°</span></div>");
		return toRet;
	}

	function setZones(r, b, d, i) {
		for (var x in r) {
			d[x].append(r[x].join(""));
			if (b[x]) { i.open(x); }
		}
	}
});
