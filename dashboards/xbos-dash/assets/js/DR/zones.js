$(document).ready(function() {
	var numZones = 20;
	var zoneRow = "<div id='loaded-zones' class='col s10'>";

	for (var i = 1; i <= numZones; i += 1) {
		zoneRow += "<div id='cb" + i + "' class='col s1 scale-transition scale-out'><label><input type='checkbox' class='filled-in my-cb' disabled='disabled' /><span class='grey-text'>" + i + "</span></label></div>";
	}
	zoneRow += "</div>";
	
	setTimeout(function() {
		$("#zone-loader").hide();
		$("#switch-label").addClass("grey-text");
		$("#zone-sel").append(zoneRow);
		$("#zone-btns").addClass("scale-in");
		var i = 0; //this way the scale-in time b/w each zone matches the one b/w the switch and the first zone
		var myIV = setInterval(function() {
			if (i > numZones) {
				clearInterval(myIV);
			} else {
				$("#cb" + i).addClass("scale-in");
				i += 1;
			}
		}, 30);
	}, 1000);

});
