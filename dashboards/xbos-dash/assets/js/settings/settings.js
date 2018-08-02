$(document).ready(function() {
	var inum = 1;
	$("#rbtn1").click(addEntry);
	function addEntry() {
		inum += 1;
		var s = "";
		s += "<div id='rec" + inum + "row' class='row valign-wrapper'>";
		s += "<div class='input-field col s3'>";
		s += "<input class='ntin rfield' type='text'>";
		s += "<label>Recipient Name</label></div>";
		s += "<div class='input-field col s3'>";
		s += "<input class='ntin rfield' type='text'>";
		s += "<label>Phone Number</label></div>";
		s += "<div class='input-field col s4'>";
		s += "<input class='ntin rfield' type='text'>";
		s += "<label>Email Address</label></div>";
		s += "<div class='col s2 center-align'>";
		s += "<a id='del" + inum + "btn' class='rbtn waves-effect waves-light btn-small red'>remove</a></div>";
		s += "</div>";
		$("#notif-card").append(s);
		$("#del" + inum + "btn").click(function() { $("#" + this.id.replace("del", "rec").replace("btn", "row")).remove(); });
	}

	function loadNotifs() {
		if (d.notifs) { notifSwitch(); }
		if (toRet.dayBefore) { $("#dayBefore").prop("checked", "checked"); }
		if (toRet.forecast) { $("#5DFC").prop("checked", "checked"); }
		for (var j = 0; j < d.recipients.length - 1; j += 1) { addEntry(); }
		var k = 0;
		var i = 1;
		var obj = d.recipients[k];
		$(".rfield").each(function() {
			if (i == 0) { i = 1; k += 1; obj = d.recipients[k]; }
			if (i == 1) { $(this).prop("value", obj.name); }
			if (i == 2) { $(this).prop("value", obj.phone); }
			if (i == 3) { $(this).prop("value", obj.email); i = -1; }
			i += 1;
		});
		M.updateTextFields();
	}
	
	var nchecked = false;
	function notifSwitch() {
		nchecked = !nchecked;
		if (nchecked) {
			$(".rbtn").each(function() { $(this).removeClass("disabled"); });
			$(".ntin").each(function() { $(this).prop("disabled", ""); });
			$(".fi-text").each(function() { $(this).removeClass("grey-text"); });
		} else {
			$(".rbtn").each(function() { $(this).addClass("disabled"); });
			$(".ntin").each(function() { $(this).prop("disabled", "disabled"); });
			$(".fi-text").each(function() { $(this).addClass("grey-text"); });
		}
		$("#notif-checkbox").prop("checked", nchecked);
	}

	$("#save-notifs").click(function() {
		var toRet = new Object();
		toRet.notifs = $("#notif-checkbox").prop("checked");
		if (!toRet.notifs) { M.toast({ html: 'Saved! You will not receive any notifications.', displayLength: 2000 }); return; }
		toRet.dayBefore = $("#dayBefore").prop("checked");
		toRet.forecast = $("#5DFC").prop("checked");
		if (!toRet.dayBefore && !toRet.forecast) { return invalid("notification"); }
		toRet.recipients = [];
		var toAdd = new Object();
		var i = 1;
		var tst = false;
		$(".rfield").each(function() {
			tst = false;
			if (i == 0) { 
				if (!toAdd.name || !toAdd.phone && !toAdd.email) { tst = true; return invalid("recipient"); }
				else { toRet.recipients.push(toAdd); toAdd = new Object(); i = 1; }
			}
			if (i == 1) { toAdd.name = $(this).prop("value"); }
			if (i == 2) { toAdd.phone = $(this).prop("value"); }
			if (i == 3) { toAdd.email = $(this).prop("value"); i = -1; }
			i += 1;
		});
		if (!toAdd.name || !toAdd.phone && !toAdd.email) { if (!tst) { return invalid("recipient"); } else { return; }}
		else { toRet.recipients.push(toAdd); }
		console.log(toRet);
		M.toast({ html: notifSummary(toRet), displayLength: 6000 });
		// return toRet;
	});

	function invalid(x) { M.toast({ html: 'Some ' + x + ' fields are missing/incomplete!', classes: 'red', displayLength: 3000 }); return false; }

	function notifSummary(x) {
		var s = "Saved! You will be notified";
		if (x.dayBefore) { s += " 1 day before confirmed events"; if (x.forecast) { s += " and for 5-day forecasts."; }}
		else if (x.forecast) { s += " for 5-day forecasts."; }
		return s;
	}

	$("#notif-div").click(function(event) { event.stopImmediatePropagation(); $("#notif-checkbox").prop("checked", nchecked); });
	$("#notif-label").click(function(event) { event.stopImmediatePropagation(); $("#notif-checkbox").prop("checked", nchecked); });
	$("#notif-checkbox").click(function(event) { event.stopImmediatePropagation(); $("#notif-checkbox").prop("checked", nchecked); });
	$("#notif-lever").click(function(event) { event.stopImmediatePropagation(); notifSwitch(); });
	$("#notif-on").click(function(event) { event.stopImmediatePropagation(); nchecked = false; notifSwitch(); });
	$("#notif-off").click(function(event) { event.stopImmediatePropagation(); nchecked = true; notifSwitch(); });
});
