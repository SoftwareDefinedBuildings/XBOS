$(document).ready(function() {
	var inum = 1;
	$("#rbtn1").click(addEntry);
	function addEntry() {
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
	}

	function loadNotifs() {
		if (d.notifs) { notifSwitch(); }
		$(".day-cb").each(function(i) { $(this).prop("checked", d.days[i].checked); });
		$(".ev-cb").each(function(i) { $(this).prop("checked", d.events[i].checked); });
		for (var j = 0; j < d.recipients.length - 1; j += 1) { addEntry(); }
		var k = 0;
		var i = 1;
		var obj = d.recipients[k];
		$(".ntin").each(function() {
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

	$("#save-notifs").click(function() {
		var toRet = new Object();
		toRet.notifs = $("#notif-checkbox").prop("checked");
		var toAdd;
		toRet.days = [];
		$(".day-cb").each(function(i) {
			i += 1;
			toAdd = new Object();
			toAdd.name = i.toString();
			toAdd.checked = $(this).prop("checked");
			toRet.days.push(toAdd);
		});

		toRet.events = [];
		$(".ev-cb").each(function() {
			toAdd = new Object();
			toAdd.name = this.id;
			toAdd.checked = $(this).prop("checked");
			toRet.events.push(toAdd);
		});
		console.log(toRet);

		toRet.recipients = [];
		toAdd = new Object();
		var i = 1;
		$(".ntin").each(function() {
			if (i == 0) { toRet.recipients.push(toAdd); toAdd = new Object(); i = 1; }
			if (i == 1) { toAdd.name = $(this).prop("value"); }
			if (i == 2) { toAdd.phone = $(this).prop("value"); }
			if (i == 3) { toAdd.email = $(this).prop("value"); i = -1; }
			i += 1;
		});
		toRet.recipients.push(toAdd);
		console.log(toRet);
		// return toRet;
	});

	$("#notifs-div").click(function(event) { event.stopImmediatePropagation(); $("#notif-checkbox").prop("checked", nchecked); });
	$("#notifs-label").click(function(event) { event.stopImmediatePropagation(); $("#notif-checkbox").prop("checked", nchecked); });
	$("#notif-checkbox").click(function(event) { event.stopImmediatePropagation(); $("#notif-checkbox").prop("checked", nchecked); });
	$("#notif-lever").click(function(event) { event.stopImmediatePropagation(); notifSwitch(); });
	$("#notifs-text").click(function(event) { event.stopImmediatePropagation(); notifSwitch(); });
});
