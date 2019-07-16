$(document).ready(function() {
	var emnum = 0;
	var rows = 1;
	$("#add-emails").click(addEntry);
	function addEntry() {
		if (rows >= 20) { M.toast({ html: 'You can only subscribe 40 users at once.', classes: 'red', displayLength: 3000 }); return; }
		rows += 1;
		$("#notif-card").append("<div id='emails-" + emnum + "' class='row valign-wrapper'><div class='input-field col s5'><input class='validate' type='email'><label>Email Address</label></div><div class='col tiny'></div><div class='input-field col s5'><input class='validate' type='email'><label>Email Address</label></div><div class='col s1-7 center-align'><a id='emails-" + emnum + "-del' class='btn-floating waves-effect waves-light red btn'><i class='material-icons'>clear</i></a></div></div>");
		$("#emails-" + emnum + "-del").click(function() { rows -= 1; $("#" + this.id.replace("-del", "")).remove(); });
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
			else if (this.value.length) { toRet.recipients.push(this.value); }
		}); if (ex) { return; }
		if (!toRet.recipients.length) { return invalid("recipient"); }
		// doSub(toRet);
	});

	function doSub(x) {
		var dep;
		$.ajax({
			"url": "http://127.0.0.1:5000/api/department",
			"type": "GET",
			"dataType": "json",
			"success": function(d) {
				dep = d.department;
			},
			"error": function(d) {
				dep = d.department;
			}
		});
		dep = "PGE";
		var ns = [];
		var s = "arn:aws:sns:us-west-2:459826155428:" + dep;
		if (x.dayBefore) { ns.push(s + "CONFIRM"); } if (x.forecast) { ns.push(s + "FORCAST"); }
		AWS.config.region = 'us-west-2';
		AWS.config.credentials = new AWS.CognitoIdentityCredentials({
			IdentityPoolId: '',
		}); var sns = new AWS.SNS({apiVersion: '2010-03-31'});
		var tarn;
		for (var i in ns) {
			tarn = ns[i];
			x.recipients.forEach(function(elem) {
				sns.subscribe({Protocol: "email", TopicArn: tarn, Endpoint: elem}, function(err, data) {
					if (err) { console.log(err, err.stack); }
					else { console.log(data); }
				});
			});
		}
		notifSummary(x);
	}

	function invalid(x) { M.toast({ html: 'Some ' + x + ' fields are missing/incorrect!', classes: 'red', displayLength: 3000 }); return false; }

	function notifSummary(x) {
		var s = "Saved! You will be notified";
		if (x.dayBefore) { s += " 1 day before confirmed events"; if (x.forecast) { s += " and for 5-day forecasts."; }}
		else if (x.forecast) { s += " for 5-day forecasts."; }
		M.toast({html: s, displayLength: 4000});
	}

});
