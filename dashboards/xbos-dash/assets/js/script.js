$(document).ready(function() {
	var dr = false;
	var soon = true;
	if (dr) {
		$("#DRROW").show();
		$("#DRTXT").addClass("white-text");
		$("#DRTXT").html("<b>Demand Response Event In Progress</b>");
		$("#DRBG").addClass("red");
		$("#DRBG").addClass("scale-in");
		$("#DRBG").addClass("pulse");
	}
	if (soon) {
		$("#DRROW").show();
		$("#DRTXT").addClass("black-text");
		$("#DRTXT").html("<b>Demand Response Event Coming Soon</b>");
		$("#DRBG").addClass("yellow");
		$("#DRBG").addClass("scale-in");
		$("#DRBG").removeClass("pulse");
	}
});