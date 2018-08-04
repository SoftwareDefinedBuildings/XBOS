$(document).ready(function() {
	let dotw = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
	setTimeout(function() { $("#forecast-loader").hide(); $("#forecast-row").css("display", "flex").show(); }, 500);

	function processResp() {
		var i = 0;
		var s = "";
		var x;
		d = {days: [{date: 1533324092, temp: 98, lvc: "unlikely"}, {date: 1533324092, temp: 98, lvc: "possible"}, {date: 1533324092, temp: 98, lvc: "likely"}, {date: 1533324092, temp: 98, lvc: "likely"}, {date: 1533324092, temp: 98, lvc: "certain"}]}
		while (i < 5) {
			x = d.days[i];
			s += "<div class='z-depth-1 center-align hoverable forecast-card " + getColor(x.lvc) + "'>";
			s += "<h6 id='date" + i + "'>" + getDate(x.date) + "</h6>";
			s += "<h3 id='temp" + i + "'>" + x.temp + "°</h3>";
			s += "<h5 id='lvc" + i + "'>DRE " + x.lvc + "</h5>";
			s += "</div>";
			i += 1;
		}
		$("#forecast-row").html(s);
	}
	processResp();

	function getColor(l) {
		if (l == "unlikely") { return "blue-grey lighten-1"}
		else if (l == "possible") { return "yellow"; }
		else if (l == "likely") { return "orange"; }
		else if (l == "certain") { return "red"; }
	}

	function getDate(e) {
		var d = new Date(0);
		d.setUTCSeconds(e);
		var x = d.toString().split(" ");
		return dotw[d.getDay()] + ", " + x[1] + " " + x[2];
	}

});
