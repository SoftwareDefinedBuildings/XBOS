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

	let l = 18;
	var s = "";
	for (var i = 1; i <= l; i += 1) {
		if (i % 2 == 1) { s += "<div class='row valign-wrapper'>"; }
		s += "<div class='col s6 z-depth-1' style='padding: 18px 30px; border-radius: 2px;'>";
		s += "<h5 class='center-align' style='margin: 0;' id='z" + i + "banner'>Zone " + i + "</h5>";
		s += "<p class='range-field'><input style='margin: 0; padding: 0;' id='z" + i + "range' class='simrange center-align' type='range' min='0' max='1' step='0.01'/></p>";
		s += "<div style='display: flex; justify-content: space-between;'>";
		s += "<h5 id='z" + i + "date' class='grey-text' style='margin-top: 0;'>Historical</h5>";
		s += "<h5 style='margin-top: 0;'>Simulated</h5>";
		s += "</div>";
		s += "<div style='display: flex;'>";
		s += "<h5 style='width: 25%; margin-top: 0;' id='z" + i + "hislam' class='grey-text left-align'>____</h5>";
		s += "<h5 class='center-align' style='width: 50%; margin-top: 0;'>λ</h5>";
		s += "<h5 class='right-align' style='width: 25%; margin-top: 0;' id='z" + i + "simlam'>____</h5>";
		s += "</div>";
		s += "<div style='display: flex;'>";
		s += "<h5 style='width: 25%; margin-top: 0;' id='z" + i + "dis' class='grey-text left-align'>____</h5>";
		s += "<h5 class='center-align' style='width: 50%; margin-top: 0;'>Discomfort</h5>";
		s += "<h5 style='width: 25%; margin-top: 0;' id='z" + i + "simdis' class='purple-text right-align text-darken-5'>____</h5>";
		s += "</div>";
		s += "<div style='display: flex;'>";
		s += "<h5 style='width: 25%; margin-top: 0;' id='z" + i + "dol' class='grey-text left-align'>____</h5>";
		s += "<h5 class='center-align' style='width: 50%; margin-top: 0;'>$ saved</h5>";
		s += "<h5 style='width: 25%; margin-top: 0;' id='z" + i + "simdol' class='green-text right-align text-darken-1'>____</h5>";
		s += "</div>";
		s += "<div style='display: flex;'>";
		s += "<h5 style='width: 25%; margin-top: 0;' id='z" + i + "kWH' class='grey-text left-align'>____</h5>";
		s += "<h5 class='center-align' style='width: 50%; margin-top: 0;'>kWH saved</h5>";
		s += "<h5 style='width: 25%; margin-top: 0;' id='z" + i + "simkWH' class='orange-text right-align text-darken-1'>____</h5>";
		s += "</div>";
		s += "</div>";
		if (i % 2 == 1) {
			if (i == l) {
				s += "<div class='col s7'></div></div>";
			} else {
				s += "<div class='col s1'></div>";
			}
		} else {
			if (i % 2 == 0) { s += "</div>"; s += "<div class='row'></div><div class='row'></div>"; }
		}
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
			// x.html("λ: " + myFix(this.value));
			x.html(myFix(this.value));
		};
	});

});
				