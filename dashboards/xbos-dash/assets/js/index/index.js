$(document).ready(function() {
	M.AutoInit();
	var elem = document.querySelector('.collapsible.expandable');
	var instance = M.Collapsible.init(elem, {
		accordion: false
	});

	var tb = true;
	$("#tempbtn").click(function() {
		var x = $(this);
		var ret = [];
		var v;
		if (tb) { y = "save"; $(".zonestemp").each(function() { $(this).replaceWith("<div class='right-align col s5 zonestemp'><input class='my-input' type='number' max=150 min=-150 value='" + $(this).html().replace("°", "") + "' /></div>"); });}
		else { y = "edit"; $(".zonestemp").each(function() { v = $(this).find("input").prop("value"); ret.push(v); $(this).replaceWith("<span class='col s5 zonestemp right-align'>" + v + "°</span>"); })}
		x.removeClass("scale-in");
		x.addClass("scale-out");
		setTimeout(function() {
			x.html("<i id='tempicon' class='material-icons right'>" + y + "</i>" + y);
			x.removeClass("scale-out");
			x.addClass("scale-in");
			clearTimeout(this);
		}, 200);
		tb = !tb;
		return ret;
	});
});


