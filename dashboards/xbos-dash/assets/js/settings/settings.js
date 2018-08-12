$(document).ready(function() {
	var emnum = 0;
	$("#add-emails").click(addEntry);
	function addEntry() {
		var s = "";
		s += "<div id='emails-" + emnum + "' class='row valign-wrapper'>";
		s += "<div class='input-field col s5'>";
		s += "<input class='validate' type='email'>";
		s += "</div>";
		s += "<div class='col tiny'></div>";
		s += "<div class='input-field col s5'>";
		s += "<input class='validate' type='email'>";
		s += "</div>";
		s += "<div class='col s1-7 center-align'>";
		s += "<a id='emails-" + emnum + "-del' class='btn-floating waves-effect waves-light red btn'><i class='material-icons'>clear</i></a>";
		s += "</div>";
		s += "</div>";
		
		$("#notif-card").append(s);
		$("#emails-" + emnum + "-del").click(function() { $("#" + this.id.replace("-del", "")).remove(); });
		emnum += 1;
	}

	$("#save-notifs").click(function() {
		var toRet = new Object();
		toRet.dayBefore = $("#dayBefore").prop("checked");
		toRet.forecast = $("#5DFC").prop("checked");
		if (!toRet.dayBefore && !toRet.forecast) { return invalid("notification"); }
		toRet.recipients = [];
		var ex = false;
		$(".validate").each(function() {
			if (!this.checkValidity()) { ex = true; return invalid("recipient"); }
			toRet.recipients.push(this.value);
		}); if (ex) { return; }
		console.log(toRet);
		// doSub(toRet);
	});

	function doSub(x) {
		var dep = "PGE";
		var ns = [];
		if (dep == "PGE") {
			if (x.dayBefore) { ns.push("arn:aws:sns:us-west-2:459826155428:PGECONFIRM"); }
			if (x.forecast) { ns.push("arn:aws:sns:us-west-2:459826155428:PGEFORCAST"); }
		} else if (dep == "SCE") {
			if (x.dayBefore) { ns.push("arn:aws:sns:us-west-2:459826155428:SCECONFIRM"); }
			if (x.forecast) { ns.push("arn:aws:sns:us-west-2:459826155428:SCEFORCAST"); }
		}
		var emails = [];
		// x.recipients.forEach(function(elem) { sendSub(ns[i], "email", elem, sns); console.log(elem); });
		// AWS.config.update({region: 'us-west-2'}); 
		// var sns = new AWS.SNS({apiVersion: '2010-03-31'});
	}

	function invalid(x) { M.toast({ html: 'Some ' + x + ' fields are missing/incorrect!', classes: 'red', displayLength: 3000 }); return false; }

	function notifSummary(x) {
		var s = "Saved! You will be notified";
		if (x.dayBefore) { s += " 1 day before confirmed events"; if (x.forecast) { s += " and for 5-day forecasts."; }}
		else if (x.forecast) { s += " for 5-day forecasts."; }
		return s;
	}

});
