$(document).ready(function() {
	M.AutoInit();
	let c = ["pink", "deep-orange", "green", "teal", "blue", "deep-purple", "tp-blue"];
	var pips = {
		mode: "count",
		values: 13,
		density: 2
	}
	var master = {
		start: [8.0, 18.0],
		connect: [true, true, true],
		range: {'min': 0, 'max': 24},
		behaviour: "tap-drag",
		pips: pips
	}
	var counts; (counts = []).length = 7; counts.fill(3);
	var sliders = [];
	var edit = false;

	$(".sched-sec").each(function(i) {
		var kids = $(this).children();
		var slider = $(kids[1]).children()[0];
		noUiSlider.create(slider, master)
		sliders.push(slider);
	});

	$("#sched-btn").click(function() {
		var x = $(this);
		x.removeClass("scale-in");
		x.addClass("scale-out");
		edit = !edit;
		if (edit) {
			var s = "save";
			sliders.forEach(function(elem) { elem.setAttribute("disabled", true); });
		} else {
			var s = "edit";
			sliders.forEach(function(elem) { elem.removeAttribute("disabled"); });
		}
		setTimeout(function() {
			x.html("<i class='large material-icons'>" + s + "</i>");
			x.removeClass("scale-out");
			x.addClass("scale-in");
			clearTimeout(this);
		}, 250);
	});

	function myfix(lst) {
		return lst.map(function(x) {
			return parseFloat(Math.floor(x)) + parseFloat(Math.floor(((x%1)+.13)/.25))*.25;
		});
	}

	function setConnects() {
		$(".noUi-connect").each(function(i) {
			$(this).unbind();
			$(this).click(function() {
				if (!edit) { return; }
				var row = 0; var sum = 0;
				while (sum < i + 1) { sum += counts[row]; row += 1; } row -= 1;
				if (row == 0) { var col = i; } else { var col = i - sum + counts[row]; }
				var s = sliders[row];
				var l = s.noUiSlider.get();
				if (!$.isArray(l)) { l = [l]; }
				else if (l.length == 6) { return; }
				l = myfix(l);
				var last = counts[row] - 1;
				if (col == 0) {
					if (l[0] <= 2.5) { l.splice(0, 0, 0.0); }
					else { l.splice(0, 0, (l[0]/2.0)); }
				} else if (col == last) {
					if (l[last - 1] >= 22.5) { l.push(24.0); }
					else { l.push((24.0 + l[last - 1])/2.0); }
				} else {
					// https://stackoverflow.com/questions/586182/how-to-insert-an-item-into-an-array-at-a-specific-index
					l.splice(col, 0, (l[col] + l[col - 1])/2.0);
				}
				l = l.map(function(x) { return x.toString(); });
				var opts = getOpts();
				opts.start = l;
				var ts; (ts = []).length = l.length + 1; ts.fill(true); opts.connect = ts;
				s.noUiSlider.destroy();
				noUiSlider.create(s, opts);
				counts[row] += 1;
				setConnects();
				setHandles();
			});
		});
	} setConnects();

	function setHandles() {
		$(".noUi-handle").each(function(i) {
			$(this).unbind();
			$(this).click(function() {
				if (!edit) { return; }
				var row = 0; var sum = 0;
				while (sum < i + 1) { sum += counts[row] - 1; row += 1; } row -= 1;
				if (row == 0) { var col = i; } else { var col = i - sum + counts[row] - 1; }
				var s = sliders[row];
				var l = s.noUiSlider.get();
				if (!$.isArray(l)) { return; }
				// https://davidwalsh.name/remove-item-array-javascript
				l.splice(col, 1);
				var opts = getOpts();
				opts.start = l;
				var ts; (ts = []).length = l.length + 1; ts.fill(true); opts.connect = ts;
				s.noUiSlider.destroy();
				noUiSlider.create(s, opts);
				counts[row] -= 1;
				setConnects();
				setHandles();
			});
		});
	} setHandles();

	function getOpts() { return {range: {'min': 0, 'max': 24}, behaviour: "none", pips: pips}; }
	
});
