$(document).ready(function() {
	M.AutoInit();
	var zoneSel = 0;
	var zoneArr = [];
	$(".filled-in").each(function() {
		$(this).click(function() {
			var t = $(this).find("span").prevObject["0"]["labels"][0]["innerText"];
			if ($(this).prop("checked")) {
				zoneSel += 1;
				zoneArr.push(t);
				console.log(zoneArr);
			} else {
				zoneSel -= 1;
				zoneArr.splice($.inArray(t, zoneArr), 1);
				console.log(zoneArr);
			}
			setGB();
		});
	});

	function setGB() {
		$("#group-btn").html("Group Selected (" + zoneSel + ")");
	}

	$("#group-btn").click(function() {
		if (zoneSel == 0) {
			$("#modal-continue").addClass("disabled");
			$("#modal-header").html("Select at least one zone to form a group");
			$("#modal-text").html("");
		} else {
			$("#modal-continue").removeClass("disabled");
			var s = "Form a group with the following ";
			if (zoneSel == 1) { s += "zone:"; } else { s += zoneSel + " zones:"; }
			$("#modal-header").html(s);
			$("#modal-text").html(zoneArr.join("<br>"));
		}
	});

});