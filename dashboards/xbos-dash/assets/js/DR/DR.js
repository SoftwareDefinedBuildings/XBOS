$(document).ready(function() {
	$("#bvz").click(function () {
		if ($("#bvz").prop("checked")) {
			x = "";
			$("#del-all").removeClass("disabled");
			$("#sel-all").removeClass("disabled");
			$(".my-cb + span").removeClass("grey-text");
			$("#switch-label").removeClass("grey-text");
			$("#zone-config").show();
			$("#bldng-config").hide();
			// $("#zone-charts").show();
			// $("#bldng-charts").hide();
		} else {
			x = "disabled";
			$("#del-all").addClass("disabled");
			$("#sel-all").addClass("disabled");
			$(".my-cb + span").addClass("grey-text");
			$("#switch-label").addClass("grey-text");
			$("#bldng-config").show();
			$("#zone-config").hide();
			// $("#bldng-charts").show();
			// $("#zone-charts").hide();
		}
		setAll("disabled", x);
	});

	function setAll(p, x) {
		$(".my-cb").each(function() {
			$(this).prop(p, x);
		});
	}

	$("#del-all").click(function() { setAll("checked", ""); });
	$("#sel-all").click(function() { setAll("checked", "checked"); });

	function myFix(x) {
		if (x > 1) {
			return x;
		}
		x = x.toString();
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

	var hlam = .9;
	var hms = 327;
	var hes = 404;
	var hdis = .8;
	$("#historic-lam").html("λ: " + myFix(hlam));
	// $("#historic-money-savings").html("$" + myFix(hms) + " saved");
	// $("#historic-savings").html("Savings: $" + myFix(hms) + " & ");
	// $("#historic-energy-savings").html(myFix(hes) + " kWH saved");
	// $("#historic-savings").append(myFix(hes) + "kWH");
	$("#historic-dis").html("Discomfort: " + myFix(hdis));
	
	// $("#historic-lam").html(myFix(hlam));
	// $("#historic-money-savings").html(myFix(hms));
	// $("#historic-energy-savings").html(myFix(hes));
	$("#historic-money-savings").html("$" + myFix(hms));
	$("#historic-energy-savings").html(myFix(hes) + "kWH");
	// $("#historic-dis").html(myFix(hdis));

	var simms = 404;
	var simes = 2122;
	// var simdis = 3;
	// $("#sim-money-savings").html("$" + myFix(simms) + " saved");
	// $("#sim-energy-savings").html(myFix(simes) + " kWH saved");
	// $("#sim-dis").html(myFix("Discomfort: " + simdis));
	
	// $("#sim-money-savings").html(myFix(simms));
	// $("#sim-energy-savings").html(myFix(simes));
	// $("#sim-dis").html(myFix(simdis));

	$("#sim-money-savings").html("$" + myFix(simms));
	$("#sim-energy-savings").html(myFix(simes) + "kWH");
	// $("#sim-dis").html(myFix("Discomfort: " + simdis));

	let b = true;
	$(".lam-range").each(function() {
		var x = $("#" + this.id.replace("-range", ""));
		this.oninput = function() {
			if (b) { $("#sim-btn").addClass("scale-in"); b = false; }
			// x.html("λ=" + myFix(this.value));
			x.html("λ: " + myFix(this.value));
			// x.html(myFix(this.value));
		}
	});

});
				