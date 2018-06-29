$(document).ready(function() {
	var checked = false;
	$("#bvz").click(mySwitch);
	function mySwitch() {
		if (checked) {
			$("#switch-bldng").addClass("black-text");
			$("#switch-zone").removeClass("black-text");
			$("#zone-config").hide();
			$("#bldng-config").show();
			$("#lever").prop("checked", false);
		} else {
			$("#switch-zone").addClass("black-text");
			$("#switch-bldng").removeClass("black-text");
			$("#bldng-config").hide();
			$("#zone-config").show();
			$("#lever").prop("checked", true);
		}
		checked = !checked;
	}

	$("#checkbox").click(function() { console.log("checkbox"); });
	$("#lever").click(function() { console.log("lever"); });
	$("#switch-zone").click(function() { console.log("switch"); });


	// $("#switch-zone").('click', function (event) {
	// 	event.stopPropagation();
	// 	$("#lever").prop("checked", true);
	// 	$("#switch-zone").addClass("black-text");
	// 	$("#switch-bldng").removeClass("black-text");
	// 	$("#bldng-config").hide();
	// 	$("#zone-config").show();
	// 	// if ($(event.target).is($("#switch-zone"))) {
	// 	// 	alert('clicked');
	// 	// }
	// });

	// $("#switch-zone").click(function() {
		// checked = false;
		// mySwitch();
	// });

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
	// $("#historic-lam").html("λ: " + myFix(hlam));
	// $("#historic-money-savings").html("$" + myFix(hms) + " saved");
	// $("#historic-energy-savings").html(myFix(hes) + " kWH saved");
	// $("#historic-savings").append(myFix(hes) + "kWH");
	// $("#historic-dis").html("Discomfort: " + myFix(hdis));
	
	$("#historic-lam").html(myFix(hlam));
	$("#historic-money-savings").html(myFix(hms));
	$("#historic-energy-savings").html(myFix(hes));
	// $("#historic-money-savings").html("$" + myFix(hms));
	// $("#historic-energy-savings").html(myFix(hes) + "kWH");
	$("#historic-dis").html(myFix(hdis));

	var simms = 404;
	var simes = 222;
	var simdis = 3;
	// $("#sim-money-savings").html("$" + myFix(simms) + " saved");
	// $("#sim-energy-savings").html(myFix(simes) + " kWH saved");
	// $("#sim-dis").html(myFix("Discomfort: " + simdis));
	
	$("#sim-money-savings").html(myFix(simms));
	$("#sim-energy-savings").html(myFix(simes));
	$("#sim-dis").html(myFix(simdis));

	// $("#sim-money-savings").html("$" + myFix(simms));
	// $("#sim-energy-savings").html(myFix(simes) + "kWH");
	// $("#sim-dis").html(myFix("Discomfort: " + simdis));

	let b = true;
	$(".lam-range").each(function() {
		var x = $("#" + this.id.replace("-range", ""));
		this.oninput = function() {
			if (b) { $("#sim-btn").addClass("scale-in"); b = false; }
			// x.html("λ=" + myFix(this.value));
			// x.html("λ: " + myFix(this.value));
			x.html(myFix(this.value));
		}
	});

});
				