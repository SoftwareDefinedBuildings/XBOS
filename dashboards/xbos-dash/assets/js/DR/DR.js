$(document).ready(function() {
	M.AutoInit();
	var checked = false;
	$("#bvz").click(mySwitch);
	function mySwitch() {
		if (checked) {
			$("#switch-bldng").addClass("black-text");
			$("#switch-zone").removeClass("black-text");
			$("#zone-config").hide();
			$("#bldng-config").show();
		} else {
			$("#switch-zone").addClass("black-text");
			$("#switch-bldng").removeClass("black-text");
			$("#bldng-config").hide();
			$("#zone-config").show();
			$("#avg-sim-btn").addClass("scale-in");
		}
		checked = !checked;
	}

	$("#my-div").click(function(event) { event.stopImmediatePropagation(); $("#checkbox").prop("checked", checked); });
	$("#label").click(function(event) { event.stopImmediatePropagation(); $("#checkbox").prop("checked", checked); });
	$("#switch-bldng").click(function(event) { event.stopImmediatePropagation(); checked = true; mySwitch(); $("#checkbox").prop("checked", checked); });
	$("#lever").click(function(event) { event.stopImmediatePropagation(); mySwitch(); });
	$("#checkbox").click(function(event) { event.stopImmediatePropagation(); $("#checkbox").prop("checked", checked); });
	$("#switch-zone").click(function(event) { event.stopImmediatePropagation(); checked = false; mySwitch(); $("#checkbox").prop("checked", checked); });

	let l = 18;
	var s = "";
	for (var i = 1; i <= l; i += 1) {
		if (i % 2 == 1) { s += "<div class='row valign-wrapper'>"; }
		s += "<div id='z" + i + "card' class='col s12 zone-card z-depth-1 hoverable' style='padding: 18px 30px; border-radius: 2px;'>";
		s += "<h6 id='z" + i + "note' style='margin: 0;'></h6>";
		s += "<h5 class='center-align' style='margin-bottom: 0;' id='z" + i + "banner'>Zone " + i + "</h5>";
		s += "<p class='range-field'><input id='z" + i + "range' class='simrange center-align' type='range' min='0' max='1' value='0.50' step='0.01'/></p>";
		s += "<div style='display: flex; justify-content: space-between;'>";
		s += "<h5 id='z" + i + "date' class='grey-text' style='margin-top: 0;'>Historical</h5>";
		s += "<h5 style='margin-top: 0;'>Simulation</h5>";
		s += "</div>";
		s += "<div style='display: flex;'>";
		s += "<h5 style='width: 25%; margin-top: 0;' id='z" + i + "hislam' class='hislam grey-text left-align'>____</h5>";
		s += "<h5 class='center-align' style='width: 50%; margin-top: 0;'>λ</h5>";
		s += "<h5 class='right-align' style='width: 25%; margin-top: 0;' id='z" + i + "simlam'>____</h5>";
		s += "</div>";
		s += "<div style='display: flex;'>";
		s += "<h5 style='width: 25%; margin-top: 0;' id='z" + i + "dis' class='hisdis grey-text left-align'>____</h5>";
		s += "<h5 class='center-align' style='width: 50%; margin-top: 0;'>Discomfort</h5>";
		s += "<h5 style='width: 25%; margin-top: 0;' id='z" + i + "simdis' class='simdis purple-text right-align text-darken-5'>5</h5>";
		s += "</div>";
		s += "<div style='display: flex;'>";
		s += "<h5 style='width: 25%; margin-top: 0;' id='z" + i + "dol' class='hisdol grey-text left-align'>____</h5>";
		s += "<h5 class='center-align' style='width: 50%; margin-top: 0;'>$ Saved</h5>";
		s += "<h5 style='width: 25%; margin-top: 0;' id='z" + i + "simdol' class='simdol green-text right-align text-darken-1'>____</h5>";
		s += "</div>";
		s += "<div style='display: flex;'>";
		s += "<h5 style='width: 25%; margin-top: 0;' id='z" + i + "kWH' class='hiskWH grey-text left-align'>____</h5>";
		s += "<h5 class='center-align' style='width: 50%; margin-top: 0;'>kWH Saved</h5>";
		s += "<h5 style='width: 25%; margin-top: 0;' id='z" + i + "simkWH' class='simkWH orange-text right-align text-darken-1'>____</h5>";
		s += "</div>";
		s += "</div>";
		if (i % 2 == 1) {
			if (i == l) {
				s += "<div class='col s7'></div></div>";
			} else {
				s += "<div class='col s1'></div>";
			}
		} else {
			if (i % 2 == 0) { s += "</div>"; s += "<div class='row'></div>"; }
		}
	}
	$("#zone-config").append(s);

	function myFix(x) {
		if (x > 1) {
			return x;
		}
		if (x == 0) {
			return "0.0";
		} else if (x == 1) {
			return "1.0";
		} else if (x.length < 4) {
			return x + "0";
		} else {
			return x;
		}
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

	// $("#sim-lam-range").each(function() {
	// 	this.onchange = function() {
	// 		$("#sim-lam-range").trigger('mouseenter');
	// 		setTimeout(function() {
	// 			$("#sim-lam-range").trigger('mouseleave');
	// 		}, 200);
	// 	}
	// 	console.log(this);
	// });

	$(".sort-li").each(function(i, v) {
		$(this).click(function() {
			console.log(i, v);
			if (i == 0) {
				$("#zad0").prop("disabled", "disabled");
				$("#zad1").prop("disabled", "disabled");
				$("#zsh0").prop("disabled", "disabled");
				$("#zsh1").prop("disabled", "disabled");
			} else {
				$("#zad0").prop("disabled", "");
				$("#zad1").prop("disabled", "");
				$("#zsh0").prop("disabled", "");
				$("#zsh1").prop("disabled", "");
			}
			$(".sort-li").each(function() { $(this).removeClass("active"); });
			$(v).addClass("active");
			$("#sort-btn").html($(this).text());
			mySort(v.id);
		});
	});

	function mySort(x) {
		var toRet = [];
		if (x == "normal") { for (var i = 1; i <= l; i += 1) { toRet.push(i); } return toRet; }
		if ($("#zsh1").prop("checked")) {
			x = "sim" + x;
		} else {
			x = "his" + x;
		}
		for (var i = 1; i <= l; i += 1) {
			var toAdd = new Object();
			toAdd.id = i;
			toAdd.val = parseFloat($("#z" + i + x).text());
			toRet.push(toAdd);
		}
		toRet.sort(myCompare);
		var r = [];
		for (var i = 0; i < l; i += 1) { r.push(toRet[i].id); }
		if ($("#zad1").prop("checked")) { r.reverse(); }
		return r;
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
			$("#" + this.id.replace("range", "card")).addClass("grey").addClass("lighten-4");
			setLamAvg();
			clearZone(this.id.replace("range", ""));
			clearSummary();
		};
	});

	function clearSummary() {
		$("#his-lam-avg").html("_____");
		$("#his-dis-avg").html("_____");
		$("#his-money-avg").html("_____");
		$("#his-energy-avg").html("_____");
		$("#sim-dis-avg").html("_____");
		$("#sim-money-avg").html("_____");
		$("#sim-energy-avg").html("_____");
	}

	function clearZone(x) {
		$("#" + x + "hislam").html("____");
		$("#" + x + "dis").html("____");
		$("#" + x + "simdis").html("____");
		$("#" + x + "dol").html("____");
		$("#" + x + "simdol").html("____");
		$("#" + x + "kWH").html("____");
		$("#" + x + "simkWH").html("____");
	}

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

	function clearBldng() {
		$("#historic-lam").html("_____");
		$("#historic-dis").html("_____");
		$("#historic-money-savings").html("_____");
		$("#historic-energy-savings").html("_____");
		$("#sim-dis").html("_____");
		$("#sim-money-savings").html("_____");
		$("#sim-energy-savings").html("_____");
	}

});
				