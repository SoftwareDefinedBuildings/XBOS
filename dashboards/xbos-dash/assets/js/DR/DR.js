$(document).ready(function() {
	M.AutoInit();
	var checked = false;
	$("#bvz").click(mySwitch);
	function mySwitch(x) {
		checked = x;
		if (checked) {
			$("#switch-bldng").addClass("black-text");
			$("#switch-zone").removeClass("black-text");
			$("#zone-chart").hide();
			$("#bldng-chart").show();
			$("#zone-config").hide();
			$("#bldng-config").show();
		} else {
			$("#switch-zone").addClass("black-text");
			$("#switch-bldng").removeClass("black-text");
			$("#bldng-chart").hide();
			$("#zone-chart").show();
			$("#bldng-config").hide();
			$("#zone-config").show();
			$("#avg-sim-btn").addClass("scale-in");
		}
		checked = !checked;
		$("#checkbox").prop("checked", checked);
	}

	$("#my-div").click(function(event) { event.stopImmediatePropagation(); $("#checkbox").prop("checked", checked); });
	$("#label").click(function(event) { event.stopImmediatePropagation(); $("#checkbox").prop("checked", checked); });
	$("#checkbox").click(function(event) { event.stopImmediatePropagation(); $("#checkbox").prop("checked", checked); });
	
	function enableBZSwitch() {
		$("#switch-bldng").unbind();
		$("#switch-bldng").click(function(event) { event.stopImmediatePropagation(); mySwitch(true); });
		$("#switch-zone").unbind();
		$("#switch-zone").click(function(event) { event.stopImmediatePropagation(); mySwitch(false); });
		$("#lever").unbind();
		$("#lever").click(function(event) { event.stopImmediatePropagation(); mySwitch(checked); });
		$("#checkbox").prop("disabled", "");
		setTextColor(checked, $("#switch-zone"), $("#switch-bldng"));
		$("#switch-zone").css("cursor", "pointer");
		$("#switch-bldng").css("cursor", "pointer");
	}
	enableBZSwitch();

	function disableBZSwitch() {
		$("#switch-bldng").unbind();
		$("#switch-bldng").click(function(event) { event.stopImmediatePropagation(); $("#checkbox").prop("checked", checked); });
		$("#switch-zone").unbind();
		$("#switch-zone").click(function(event) { event.stopImmediatePropagation(); $("#checkbox").prop("checked", checked); });
		$("#lever").unbind();
		$("#lever").click(function(event) { event.stopImmediatePropagation(); $("#checkbox").prop("checked", checked); });
		$("#checkbox").prop("disabled", "disabled");
		$("#switch-zone").removeClass("black-text");
		$("#switch-bldng").removeClass("black-text");
		$("#switch-zone").css("cursor", "default");
		$("#switch-bldng").css("cursor", "default");
	}

	function asDesSwitch(x) {
		if (sb != "normal") {
			asDesChecked = x;
			$("#as-des-checkbox").prop("checked", asDesChecked);
			setTextColor(asDesChecked, $("#switch-des"), $("#switch-as"));
			mySort(sb);
		}
	}

	function simHisSwitch(x) {
		if (sb != "normal") {
			simHisChecked = x;
			$("#sim-his-checkbox").prop("checked", simHisChecked);
			setTextColor(simHisChecked, $("#switch-his"), $("#switch-sim"));
			mySort(sb);
		}
	}

	function setTextColor(x, a, b) {
		if (x) { a.addClass("black-text"); b.removeClass("black-text"); }
		else { a.removeClass("black-text"); b.addClass("black-text"); }
	}

	function disableSwitches() {
		$("#as-des-checkbox").prop("disabled", "disabled");
		$("#sim-his-checkbox").prop("disabled", "disabled");
		$(".mySwitch").each(function() { $(this).css("cursor", "default"); });
		$(".mySwitch").each(function() { $(this).removeClass("black-text"); });
	}

	function enableSwitches() {
		$("#as-des-checkbox").prop("disabled", "");
		$("#sim-his-checkbox").prop("disabled", "");
		setTextColor(asDesChecked, $("#switch-des"), $("#switch-as"));
		setTextColor(simHisChecked, $("#switch-his"), $("#switch-sim"));
		$(".mySwitch").each(function() { $(this).css("cursor", "pointer"); });
	}

	var asDesChecked = false;
	$("#as-des-div").click(function(event) { event.stopImmediatePropagation(); $("#as-des-checkbox").prop("checked", asDesChecked); });
	$("#as-des-label").click(function(event) { event.stopImmediatePropagation(); $("#as-des-checkbox").prop("checked", asDesChecked); });
	$("#as-des-checkbox").click(function(event) { event.stopImmediatePropagation(); $("#as-des-checkbox").prop("checked", asDesChecked); });
	$("#switch-as").click(function(event) { event.stopImmediatePropagation(); asDesSwitch(false); });
	$("#switch-des").click(function(event) { event.stopImmediatePropagation(); asDesSwitch(true); });
	$("#as-des-lever").click(function(event) { event.stopImmediatePropagation(); asDesSwitch(!asDesChecked); });

	var simHisChecked = false;
	$("#sim-his-div").click(function(event) { event.stopImmediatePropagation(); $("#sim-his-checkbox").prop("checked", simHisChecked); });
	$("#sim-his-label").click(function(event) { event.stopImmediatePropagation(); $("#sim-his-checkbox").prop("checked", simHisChecked); });
	$("#sim-his-checkbox").click(function(event) { event.stopImmediatePropagation(); $("#sim-his-checkbox").prop("checked", simHisChecked); });
	$("#switch-sim").click(function(event) { event.stopImmediatePropagation(); simHisSwitch(false); });
	$("#switch-his").click(function(event) { event.stopImmediatePropagation(); simHisSwitch(true); });
	$("#sim-his-lever").click(function(event) { event.stopImmediatePropagation(); simHisSwitch(!simHisChecked); });

	let l = 17;
	var s = "";
	s += "<div class='row' style='display: flex; flex-wrap: wrap; justify-content: space-between;'>";
	for (var i = 0; i < l; i += 1) {
		s += "<div id='z" + i + "card' class='col s5-5 zone-card z-depth-1 hoverable lighten-4' style='padding: 18px 30px; order: " + i + "; margin-bottom: 26px;'>";
		s += "<h6 id='z" + i + "note' class='znote' style='margin: 0;'></h6>";
		s += "<h4 class='center-align' style='margin-bottom: 0;' id='z" + i + "banner'>Zone " + i + "</h4>";
		s += "<p class='range-field'><input id='z" + i + "range' class='simrange center-align' type='range' min='0' max='1' value='0.50' step='0.01'/></p>";
		s += "<div style='display: flex; justify-content: space-between;'>";
		s += "<h5 id='z" + i + "date' class='grey-text' style='margin-top: 0;'>Historical</h5>";
		s += "<h5 style='margin-top: 0;'>Simulation</h5>";
		s += "</div>";
		s += "<div style='display: flex;'>";
		s += "<h5 style='width: 25%; margin-top: 0;' id='z" + i + "hislam' class='z" + i + "-val hislam grey-text left-align'>____</h5>";
		s += "<h5 class='center-align' style='width: 50%; margin-top: 0;'>λ</h5>";
		s += "<h5 class='right-align' style='width: 25%; margin-top: 0;' id='z" + i + "simlam'>0.50</h5>";
		s += "</div>";
		s += "<div style='display: flex;'>";
		s += "<h5 style='width: 25%; margin-top: 0;' id='z" + i + "hisdis' class='z" + i + "-val hisdis grey-text left-align'>____</h5>";
		s += "<h5 class='center-align' style='width: 50%; margin-top: 0;'>Discomfort</h5>";
		s += "<h5 style='width: 25%; margin-top: 0;' id='z" + i + "simdis' class='z" + i + "-val simdis purple-text right-align text-darken-5'>____</h5>";
		s += "</div>";
		s += "<div style='display: flex;'>";
		s += "<h5 style='width: 25%; margin-top: 0;' id='z" + i + "hisdol' class='z" + i + "-val hisdol grey-text left-align'>____</h5>";
		s += "<h5 class='center-align' style='width: 50%; margin-top: 0;'>$ Saved</h5>";
		s += "<h5 style='width: 25%; margin-top: 0;' id='z" + i + "simdol' class='z" + i + "-val simdol green-text right-align text-darken-1'>____</h5>";
		s += "</div>";
		s += "<div style='display: flex;'>";
		s += "<h5 style='width: 25%; margin-top: 0;' id='z" + i + "hiskWH' class='z" + i + "-val hiskWH grey-text left-align'>____</h5>";
		s += "<h5 class='center-align' style='width: 50%; margin-top: 0;'>kWH Saved</h5>";
		s += "<h5 style='width: 25%; margin-top: 0;' id='z" + i + "simkWH' class='z" + i + "-val simkWH orange-text right-align text-darken-1'>____</h5>";
		s += "</div>";
		s += "</div>";
	}
	s += "</div>";
	$("#zone-config").append(s);

	function myFix(x) {
		if (x > 1) { return x; }
		if (x == 0) { return "0.0"; }
		if (x == 1) { return "1.0"; }
		x = x.toString();
		if (x.length < 4) { return x + "0"; }
		return x;
	}

	let b = true;
	$("#sim-lam-range").each(function() {
		var x = $("#sim-lam");
		this.oninput = function() {
			if (b) { $("#sim-btn").addClass("scale-in"); b = false; };
			x.html(myFix(this.value));
			clearBldng();
		};
	});

	var sb = "normal";
	$(".sort-li").each(function(i, v) {
		$(this).click(function() {
			$(".sort-li").each(function() { $(this).removeClass("active"); });
			$(v).addClass("active");
			sb = v.id;
			mySort(v.id);
			$("#sort-btn").text($(v).children().text());
		});
	});

	function mySort(x) {
		var r = [];
		if (x == "normal") {
			disableSwitches();
			for (var i = 0; i < l; i += 1) { r.push(i); }
		} else {
			enableSwitches();
			var toRet = [];
			if (!simHisChecked) { x = "sim" + x; } else { x = "his" + x; }
			for (var i = 0; i < l; i += 1) {
				var toAdd = new Object();
				toAdd.id = i;
				toAdd.val = parseFloat($("#z" + i + x).text());
				toRet.push(toAdd);
			}
			toRet.sort(myCompare);
			for (var i = 0; i < l; i += 1) { r.push(toRet[i].id); }
			if (asDesChecked) { r.reverse(); }
		}
		for (var i = 0; i < l; i += 1) { $("#z" + r[i] + "card").css("order", i); }
	}
	
	// https://stackoverflow.com/posts/1129270
	function myCompare(a, b) {
		if (a.val < b.val) { return -1; }
		if (a.val > b.val) { return 1; }
		return 0;
	}

	$(".simrange").each(function() {
		var x = $("#" + this.id.replace("range", "simlam"));
		this.oninput = function() {
			x.html(myFix(this.value));
			$("#" + this.id.replace("range", "card")).addClass("grey");
			setLamAvg();
			clearZone(this.id.replace("range", ""));
			clearSummary();
		};
	});

	$("#bldng-btn").click(function() {
		$("#bldng-config").hide();
		$("#sim-loader").show();
		// https://stackoverflow.com/questions/2275274/
		setTimeout(function() { $('html, body').animate({ scrollTop: '0px' }, 200) }, 10);
		disableBZSwitch();
		M.toast({html: 'Please allow the simulation a few minutes <button id="cancel-sim" class="btn-flat toast-action">Cancel</button>', displayLength: 25000});
		$("#cancel-sim").click(function() { $("#sim-loader").hide(); $("#bldng-config").show(); M.Toast.dismissAll(); });
		var toRet = new Object();
		toRet.isBuilding = true;
		toRet.lam = parseFloat($("#sim-lam-range").prop("value"));
		bldngChart.setTitle({ text: "Simulated vs Baseline" }, { text: "Simulated streams are dotted" });
		
		console.log(toRet);
		return toRet;
	});

	$("#zone-btn").click(function() {
		$("#zone-config").hide();
		$("#sim-loader").show();
		// https://stackoverflow.com/questions/2275274/
		setTimeout(function() { $('html, body').animate({ scrollTop: '0px' }, 200) }, 10);
		disableBZSwitch();
		M.toast({html: 'Please allow the simulation a few minutes <button id="cancel-sim" class="btn-flat toast-action">Cancel</button>', displayLength: 60000});
		$("#cancel-sim").click(function() {
			postSim();
			$(".znote").each(function() { $(this).html(""); });
		});
		var toRet = new Object();
		toRet.isBuilding = false;
		toRet.lam = [];
		var toAdd;
		var notes = [];
		$(".simrange").each(function(i) {
			toAdd = new Object();
			toAdd.id = i;
			toAdd.val = parseFloat($(this).prop("value"));
			toRet.lam.push(toAdd);
			notes.push(toAdd.val);
		});
		setTimeout(function() {
			simSuccess();
			var i = 0;
			$(".znote").each(function() { $(this).html("values shown are for λ=" + myFix(notes[i])); i += 1; });
		}, 3000);
	});

	function simSuccess() {
		zoneChart.setTitle({ text: "Simulated vs Baseline" }, { text: "Simulated streams are dotted" });
		$(".zone-card").each(function() { $(this).removeClass("grey"); });
		postSim();
	}

	function postSim() {
		M.Toast.dismissAll();
		$("#sim-loader").hide();
		$("#zone-config").show();
		enableBZSwitch();
	}
	



	// function setSummary() {

	// }

	// function setZone(x, obj) {

	// }

	// function setBldng() {

	// }

	function clearSummary() { $(".sum-val").each(function() { $(this).html("_____"); });}
	function clearZone(x) { $(".z" + x + "-val").each(function() { $(this).html("____"); });}
	function clearBldng() { $(".bldng-val").each(function() { $(this).html("_____"); });}

	function setSummaryVals() {
		setSumVal(".hislam", "#his-lam-avg", true);
		setSumVal(".hisdis", "#his-dis-avg", true);
		setSumVal(".simdis", "#sim-dis-avg", true);
		setSumVal(".hisdol", "#his-money-avg", false);
		setSumVal(".simdol", "#sim-money-avg", false);
		setSumVal(".hiskWH", "#his-energy-avg", false);
		setSumVal(".simkWH", "#sim-energy-avg", false);
	}

	function setLamAvg() {
		var x = 0;
		$(".simrange").each(function() { x += parseFloat(this.value); });
		x = x / l.toFixed(2);
		$("#sim-lam-avg").html(myFix(x.toFixed(2)));
	}

	function setSumVal(s, k, b) {
		var x = 0;
		$(s).each(function() { x += parseFloat($("#" + this.id).html()); });
		if (b) { x = x / l.toFixed(2); }
		$(k).html(myFix(x.toFixed(2)));
	}
});
				