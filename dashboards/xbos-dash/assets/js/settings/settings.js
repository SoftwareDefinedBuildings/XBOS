$(document).ready(function() {
	var nchecked = false;
	function notifSwitch() {
		nchecked = !nchecked;
		if (nchecked) {
			$(".rbtn").each(function() { $(this).removeClass("disabled"); });
			$(".ntin").each(function() { $(this).prop("disabled", ""); });
			$(".filled-in").each(function() { $(this).prop("disabled", ""); });
			$(".fi-text").each(function() { $(this).removeClass("grey-text"); });
		} else {
			$(".rbtn").each(function() { $(this).addClass("disabled"); });
			$(".ntin").each(function() { $(this).prop("disabled", "disabled"); });
			$(".filled-in").each(function() { $(this).prop("disabled", "disabled"); });
			$(".fi-text").each(function() { $(this).addClass("grey-text"); });
		}
		$("#notif-checkbox").prop("checked", nchecked);
	}

	var inum = 1;
	$("#rbtn1").click(function() {
		inum += 1;
		var s = "";
		s += "<div id='rec" + inum + "row' class='row valign-wrapper'>";
		s += "<div class='input-field col s3'>";
		s += "<input class='ntin' type='text'>";
		s += "<label>Recipient Name</label></div>";
		s += "<div class='input-field col s3'>";
		s += "<input class='ntin' type='text'>";
		s += "<label>Phone Number</label></div>";
		s += "<div class='input-field col s4'>";
		s += "<input class='ntin' type='text'>";
		s += "<label>Email Address</label></div>";
		s += "<div class='col s2 center-align'>";
		s += "<a id='del" + inum + "btn' class='rbtn waves-effect waves-light btn-small red'>remove</a></div>";
		s += "</div>";
		$("#notif-card").append(s);
		$("#del" + inum + "btn").click(function() { $("#" + this.id.replace("del", "rec").replace("btn", "row")).remove(); });
	});

	$("#save-notifs").click(function() {
		var toRet = new Object();
		toRet.name = "Notification Recipients";
		toRet.data = [];
		var toAdd = new Object();
		var i = 1;
		$(".ntin").each(function() {
			if (i == 0) { toRet.data.push(toAdd); toAdd = new Object(); i = 1; }
			if (i == 1) { toAdd.name = $(this)[0].value; }
			if (i == 2) { toAdd.phone = $(this)[0].value; }
			if (i == 3) { toAdd.email = $(this)[0].value; i = -1; }
			i += 1;
		});
		toRet.data.push(toAdd);
		console.log(toRet);
		return toRet;
	});

	$("#notifs-div").click(function(event) { event.stopImmediatePropagation(); $("#notif-checkbox").prop("checked", nchecked); });
	$("#notifs-label").click(function(event) { event.stopImmediatePropagation(); $("#notif-checkbox").prop("checked", nchecked); });
	$("#notif-checkbox").click(function(event) { event.stopImmediatePropagation(); $("#notif-checkbox").prop("checked", nchecked); });
	$("#notif-lever").click(function(event) { event.stopImmediatePropagation(); notifSwitch(); });
	$("#notifs-text").click(function(event) { event.stopImmediatePropagation(); notifSwitch(); });
});
