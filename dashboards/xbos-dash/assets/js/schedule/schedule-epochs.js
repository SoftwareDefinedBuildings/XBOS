$(document).ready(function() {
	M.AutoInit();
	let c = ["pink", "deep-orange", "green", "teal", "blue", "deep-purple", "tp-blue"];
	let pipvals = ["12am", "2am", "4am", "6am", "8am", "10am", "12pm", "2pm", "4pm", "6pm", "8pm", "10pm", "12am"];
	let piprev = ["12am", "10pm", "8pm", "6pm", "4pm", "2pm", "12pm", "10am", "8am", "6am", "4am", "2am", "12am"];

	pips = {
		mode: "values",
		values: [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24],
		density: 2
	}

	function getMaster() {
		return {
			start: [8.0, 18.0],
			connect: [true, true, true],
			range: {'min': 0.0, 'max': 24.0},
			step: .25,
			behaviour: "tap-drag"
		}
	}

	var counts; (counts = []).length = 7; counts.fill(3);
	var sliders = [];

	$(".sched-slider").each(function(i) {
		var master = getMaster();
		if (i == 0 || i == 6) { master.pips = pips; }
		noUiSlider.create(this, master);
		sliders.push(this);
	});

	function setTop() {
		$(".noUi-pips-horizontal").each(function(i) {
			if (i == 0) {
				$(this).css("top", "-80px").css("transform", "rotate(180deg)");
				$(".noUi-value-large").each(function(j) {
					if (j < 13) { $(this).css("transform", "rotate(180deg)").css("margin-left", "-17px").css("margin-top", "16px"); }
				});
				$('.noUi-value.noUi-value-horizontal.noUi-value-large').each(function(j) {
					var l = pipvals;
					if (j < 13) { l = piprev; }
					$(this).html(l[j % 13]);
				});
			}
		});
	} setTop();

	var edit = false;
	function schedClick(c=true) {
		var x = $("#sched-btn");
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
		if (c && mode) { mode = true; editModes(false); }
	} $("#sched-btn").click(schedClick);

	function myfix(lst) {
		return lst.map(function(x) {
			return parseFloat(Math.floor(x)) + parseFloat(Math.floor(((x%1)+.13)/.25))*.25;
		});
	}

	function getConnect() {
		$(".noUi-connect").each(function(i) {
			$(this).click(function() {
				var row = 0; var sum = 0;
				while (sum < i + 1) { sum += counts[row]; row += 1; } row -= 1;
				if (row == 0) { var col = i; } else { var col = i - sum + counts[row]; }
				console.log(row, col);
			});
			console.log($(this));
		});
	} getConnect();

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
				else if (l.length == 5) { return; }
				l = l.map(function(x) { return parseFloat(x); });
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
				var opts = getMaster();
				opts.start = l;
				var ts; (ts = []).length = l.length + 1; ts.fill(true); opts.connect = ts;
				if (row == 0 || row == 6) {
					opts.pips = pips;
				}
				s.noUiSlider.destroy();
				noUiSlider.create(s, opts);
				counts[row] += 1;
				setConnects();
				setHandles();
				setTop();
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
				var opts = getMaster();
				opts.start = l;
				var ts; (ts = []).length = l.length + 1; ts.fill(true); opts.connect = ts;
				if (row == 0 || row == 6) {
					opts.pips = pips;
				}
				s.noUiSlider.destroy();
				noUiSlider.create(s, opts);
				counts[row] -= 1;
				setConnects();
				setHandles();
				setTop();
			});
		});
	} setHandles();

	function getOpts() { return {range: {'min': 0.0, 'max': 24.0}, step: .25, behaviour: "tap-drag"}; }

	// $($("#rando").parents()[2]).addClass("grey");

});
