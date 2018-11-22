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
			behaviour: "drag"
		}
	}

	var counts; (counts = []).length = 7; counts.fill(3);
	var sliders = [];
	var sliderColors = [["#CCC", "#CCC", "#CCC"],["#CCC", "#CCC", "#CCC"],
						["#CCC", "#CCC", "#CCC"],["#CCC", "#CCC", "#CCC"],
						["#CCC", "#CCC", "#CCC"],["#CCC", "#CCC", "#CCC"],
						["#CCC", "#CCC", "#CCC"]];
	var sliderModes = [[null, null, null],[null, null, null],
						[null, null, null],[null, null, null],
						[null, null, null],[null, null, null],
						[null, null, null]];

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

	var dissed = false;
	var edit = false;
	function schedClick(c=true) {
		var x = $("#sched-btn");
		x.removeClass("scale-in");
		x.addClass("scale-out");
		edit = !edit;
		if (edit) {
			var s = "save";
			if (c) { sliders.forEach(function(elem) { elem.setAttribute("disabled", true); });}
			dissed = true;
		} else {
			var s = "edit";
			if (c) { sliders.forEach(function(elem) { elem.removeAttribute("disabled"); });}
			dissed = false;
		}
		setTimeout(function() {
			x.html("<i class='large material-icons right'>" + s + "</i>" + s);
			x.removeClass("scale-out");
			x.addClass("scale-in");
			clearTimeout(this);
		}, 250);
		if (c && mode) { editModes(false); }
	} $("#sched-btn").click(schedClick);

	function myfix(lst) {
		return lst.map(function(x) {
			return parseFloat(Math.floor(x)) + parseFloat(Math.floor(((x%1)+.13)/.25))*.25;
		});
	}

	var colors = ["#3B7EA1", "#FDB515", "#cab2d6", "#fccde5", "#b2df8a"];
	var curMode = 0;
	var curColor = colors[0];
	$(".with-gap").each(function(i) {
		$(this).click(function() {
			curMode = i;
			curColor = colors[i];
		});
	});

	function getConnect() {
		$(".noUi-connect").each(function(i) {
			$(this).click(function() {
				var row = 0; var sum = 0;
				while (sum < i + 1) { sum += counts[row]; row += 1; } row -= 1;
				if (row == 0) { var col = i; } else { var col = i - sum + counts[row]; }
				if (!edit) {
					if (sliderColors[row][col] == curColor) {
						$(this).css("background", "#CCC");
						sliderColors[row][col] = "#CCC";
						sliderModes[row][col] = null;
					} else {
						$(this).css("background", curColor);
						sliderColors[row][col] = curColor;
						sliderModes[row][col] = curMode;
					}
					console.log(sliderColors);
				}
				console.log(row, col);
			});
		});
	} getConnect();

	var location;
	function readIn() {
		location = "Basketball Courts";
		$("#location").append(location);
	} readIn();

	function readOut() {
		var obj = new Object();
		obj.name = location;
		obj.zones = [1, 3, 5, 7];
		obj.modes = [];
		$(".mode-card").each(function(i) {
			var m = new Object();
			m.id = i;
			var inputs = $(this).find("input");
			m.name = inputs[0].value;
			m.heating = inputs[1].value;
			m.cooling = inputs[2].value;
			m.enabled = $(inputs[3]).prop("checked");
			obj.modes.push(m);
		});
		var sched = new Object();
		var t = new Object();
		t.sun = $.extend([], sliders[0].noUiSlider.get());
		t.mon = $.extend([], sliders[1].noUiSlider.get());
		t.tue = $.extend([], sliders[2].noUiSlider.get());
		t.wed = $.extend([], sliders[3].noUiSlider.get());
		t.thu = $.extend([], sliders[4].noUiSlider.get());
		t.fri = $.extend([], sliders[5].noUiSlider.get());
		t.sat = $.extend([], sliders[6].noUiSlider.get());
		sched.times = t;
		var sets = new Object();
		sets.sun = sliderModes[0];
		sets.mon = sliderModes[1];
		sets.tue = sliderModes[2];
		sets.wed = sliderModes[3];
		sets.thu = sliderModes[4];
		sets.fri = sliderModes[5];
		sets.sat = sliderModes[6];
		sched.settings = sets;
		obj.schedule = sched;
		console.log(obj);
	}

	$("#apply-modes").click(function() {
		M.toast({html: 'Preferences saved and modes applied.', classes:"rounded", displayLength: 5000});
		readOut();
	});

	function setColors() {
		$(".noUi-connect").each(function(i) {
			var row = 0; var sum = 0;
			while (sum < i + 1) { sum += counts[row]; row += 1; } row -= 1;
			if (row == 0) { var col = i; } else { var col = i - sum + counts[row]; }
			$(this).css("background", sliderColors[row][col]);
		});
	} setColors();

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
				else if (l.length == 5) {
					M.toast({html: "You must first press save", classes: "rounded", displayLength: 5000});
					return;
				}
				l = l.map(function(x) { return parseFloat(x); });
				var last = counts[row] - 1;
				if (col == 0) {
					if (l[0] <= 2.5) { l.splice(0, 0, 0.0); }
					else { l.splice(0, 0, (l[0]/2.0)); }
					sliderColors[row].splice(0, 0, sliderColors[row][0]);
					sliderModes[row].splice(0, 0, sliderModes[row][0]);
				} else if (col == last) {
					if (l[last - 1] >= 22.5) { l.push(24.0); }
					else { l.push((24.0 + l[last - 1])/2.0); }
					sliderColors[row].push(sliderColors[row][sliderColors[row].length - 1]);
					sliderModes[row].push(sliderModes[row][sliderModes[row].length - 1]);
				} else {
					// https://stackoverflow.com/questions/586182/how-to-insert-an-item-into-an-array-at-a-specific-index
					l.splice(col, 0, (l[col] + l[col - 1])/2.0);
					sliderColors[row].splice(col, 0, sliderColors[row][col]);
					sliderModes[row].splice(col, 0, sliderModes[row][col]);
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
				setColors();
				setConnects();
				setHandles();
				setTop();
				getConnect();
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
				console.log(row, col);
				// https://davidwalsh.name/remove-item-array-javascript
				l.splice(col, 1);
				if (sliderColors[row][col] == sliderColors[row][col+1]) {
					sliderColors[row].splice(col, 1);
					sliderModes[row].splice(col, 1);
				} else {
					sliderColors[row].splice(col, 2, "#CCC");
					sliderModes[row].splice(col, 2, null);
				}
				var opts = getMaster();
				opts.start = l;
				var ts; (ts = []).length = l.length + 1; ts.fill(true); opts.connect = ts;
				if (row == 0 || row == 6) {
					opts.pips = pips;
				}
				s.noUiSlider.destroy();
				noUiSlider.create(s, opts);
				counts[row] -= 1;
				setColors();
				setConnects();
				setHandles();
				setTop();
				getConnect();
			});
		});
	} setHandles();

	getConnect();

	function getOpts() { return {range: {'min': 0.0, 'max': 24.0}, step: .25, behaviour: "tap-drag"}; }

	// $($("#rando").parents()[2]).addClass("grey");

	var mode = false;
	function editModes(c=true) {
		var x = $("#mode-edit");
		x.removeClass("scale-in");
		x.addClass("scale-out");
		mode = !mode;
		if (mode) {
			$("#mode-radios").show();
			if (c) { sliders.forEach(function(elem) { elem.setAttribute("disabled", true); });}
			var s = "save";
			dissed = true;
		} else {
			$("#mode-radios").hide();
			if (c) { sliders.forEach(function(elem) { elem.removeAttribute("disabled"); });}
			var s = "edit";
			dissed = false;
		}
		setTimeout(function() {
			x.html("<i class='large material-icons right'>" + s + "</i>" + s);
			x.removeClass("scale-out");
			x.addClass("scale-in");
			clearTimeout(this);
		}, 250);
		if (c && edit) { schedClick(false); }
	} $("#mode-edit").click(editModes);

	function getEdit() { if (mode) { return "save"; } else { return "edit"; }}

	// var modenum = 3;
	// var colors = ["#3B7EA1", "#FDB515", "#cab2d6", "#fccde5", "#b2df8a"];
	// var curColor = colors[0];
	// $(".with-gap").each(function(i) {
	// 	$(this).click(function() {
	// 		curColor = colors[i];
	// 	});
	// });

	// function addMode() {
	// 	$("#mode-btn-div").remove();
	// 	$("#mode-stq").remove();
	// 	$("#mode-div").append("<div style='background-color:" + colors[modenum] + ";' class='col s2 z-depth-1 mode-card'><input style='padding: 12px 0 7px 0;' id='mode" + modenum + "' type='text' maxlength='10' placeholder='Mode Name' class='my-input mode-title' /><div class='setpnt-div'><input class='red lighten-2 spl' value=55 type='number' max='72' min='35' /><input class='blue lighten-2 spr' value=85 type='number' max='90' min='74' /></div><div class='switch'><label><input class='ogswitch' type='checkbox'><span class='lever'></span></label></div></div>");
	// 	$("#mode-radios").append("<div class='col s2'><label><input class='with-gap' name='group1' type='radio' /><span style='margin-left: 5px;'></span></label></div>");
	// 	modenum += 1;
	// 	$("#mode-div").append("<div id='mode-btn-div' class='col stq'><a id='mode-btn' class='btn btn-floating waves-effect waves-light'><i class='large material-icons'>add</i></a><div class='row'></div><a id='mode-edit' class='btn btn-floating waves-effect waves-light blue scale-transition'><i class='large material-icons'>" + getEdit() + "</i></a></div>");
	// 	$("#mode-radios").append("<div id='mode-stq' class='col stq'></div>");
	// 	if (modenum == 5) { $("#mode-btn").addClass("disabled"); }
	// 	$("#mode-edit").click(editModes);
	// 	$("#mode-btn").click(addMode);
	// 	// checkModes();
	// } $("#mode-btn").click(addMode);

	// function checkModes() {
	// 	if (modenum > 3) {
	// 		$("#first-mode").css("margin-left", "0");
	// 		$("#first-radio").css("margin-left", "0");
	// 	} else {
	// 		$("#first-mode").css("margin-left", "auto");
	// 		$("#first-radio").css("margin-left", "auto");
	// 	}
	// }

});
