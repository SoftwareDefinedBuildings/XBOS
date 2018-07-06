$(document).ready(function() {
	var checked = false;
	$("#bvz").click(mySwitch);
	function mySwitch() {
		if (checked) {
			$("#switch-bldng").addClass("black-text");
			$("#switch-zone").removeClass("black-text");
			$("#zone-config").hide();
			$("#bldng-config").show();
			// $("#lever").prop("checked", false);
		} else {
			$("#switch-zone").addClass("black-text");
			$("#switch-bldng").removeClass("black-text");
			$("#bldng-config").hide();
			$("#zone-config").show();
			// $("#lever").prop("checked", true);
		}
		checked = !checked;
	}

	let l = 10;
	var s = "";
	for (var i = 0; i < l; i += 1) {
		s += "<span id='z" + i + "banner' style='font-size: 28px;'>Zone " + (i+1) + "</span>";
		s += "<div class='row center-align valign-wrapper z-depth-1' style='border-radius: 2px;'>";
		s += "<div class='col s6'>";
		s += "<div style='display: flex;'>";
		s += "<h5 id='z" + i + "hislam' style='width: 33%;' class='grey-text left-align'></h5>";
		s += "<h5 id='z" + i + "simlam' style='width: 34%; margin-right: 33%;'>λ</h5>";
		s += "</div>";
		s += "<p class='range-field'><input id='z" + i + "range' class='simrange center-align' type='range' min='0' max='1' step='0.01'/></p>";
		s += "</div>";
		s += "<div class='col s3'>";
		// s += "<h5 id='z" + i + "date' class='grey-text' style='margin-top: 0;'>Historical</h5>";
		s += "<h6 id='z" + i + "dis' class='grey-text' style='margin: 0;'>_____</h6>";
		s += "<h6 id='z" + i + "dol' class='grey-text'>_____</h6>";
		s += "<h6 id='z" + i + "kWH' class='grey-text' style='margin-bottom: 0;'>_____</h6>";
		s += "</div>";
		s += "<div class='col s3'>";
		// s += "<h5 style='margin-top: 0;'>Simulated</h5>";
		s += "<h6 id='z" + i + "simdis' class='purple-text text-darken-5' style='margin: 0;'>_____</h6>";
		s += "<h6 id='z" + i + "simdol' class='green-text text-darken-1'>_____</h6>";
		s += "<h6 id='z" + i + "simkWH' class='orange-text text-darken-1' style='margin-bottom: 0;'>_____</h6>";
		s += "</div>";
		s += "</div>";
		s += "<div class='row'></div>";
		s += "<div class='row'></div>";
	}
	$("#zone-config").append(s);


	// $("#checkbox").click(function() { console.log("checkbox"); });
	// $("#lever").click(function() { console.log("lever"); });
	// $("#switch-zone").click(function() { console.log("switch"); });

	$("#lever").click(mySwitch);

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
	// 	// checked = false;
	// 	mySwitch();
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

	let b = true;
	$("#sim-lam-range").each(function() {
		var x = $("#sim-lam");
		this.oninput = function() {
			if (b) { $("#sim-btn").addClass("scale-in"); b = false; };
			x.html(myFix(this.value));
		};
	});


	$(".simrange").each(function() {
		var x = $("#" + this.id.replace("range", "simlam"));
		this.oninput = function() {
			x.html("λ: " + myFix(this.value));
		};
	});

});
				