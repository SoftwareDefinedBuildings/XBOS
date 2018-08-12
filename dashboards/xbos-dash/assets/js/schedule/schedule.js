$(document).ready(function() {
	let c = ["pink", "deep-orange", "green", "teal", "blue", "deep-purple", "tp-blue"];
	var pips = {
		mode: "count",
		values: 13,
		density: 2
	}
	var master = {
		start: [1.0, 8.0, 18.0, 23.0],
		connect: [true, true, true, true, true],
		range: {'min': 0, 'max': 24},
		behaviour: "none",
		pips: pips
	}
	var counts; (counts = []).length = 7; counts.fill(5);

	$(".sched-sec").each(function(i) {
		// console.log(this);
		var kids = $(this).children();
		var addbtn = $(kids[0]).children();
		var slider = $(kids[1]).children()[0];
		// console.log(slider);
		noUiSlider.create(slider, master)
		var delbtn = $(kids[2]).children();
		// console.log(i);

		addbtn.click(function() {
			var lst = slider.noUiSlider.get();
			var ind;
			if (!$.isArray(lst)) { lst = $.merge([lst], [24.0]); }
			else {
				lst = lst.map(function(x) { return parseFloat(x); });
				if (lst.length == 2) { ind = (lst[0] + lst[1])/2.0; } else if (lst.length >= 6) { return; }
				else { ind = (lst[Math.floor(lst.length/2)] + lst[Math.floor(lst.length/2) + 1])/2.0; }
				lst.push(ind);
				lst.sort(function(a, b) { return a - b; });
			}
			// https://stackoverflow.com/questions/18307253/how-to-sort-an-array-of-floats-in-javascript
			var opts = master;
			opts.start = lst;
			var ts; (ts = []).length = lst.length + 1; ts.fill(true); opts.connect = ts;
			slider.noUiSlider.destroy();
			noUiSlider.create(slider, opts);
			console.log(i);
			counts[i] = lst.length + 1;
			setConnects();
			console.log(counts);
			// console.log(myfix(lst));
		});

		delbtn.click(function() {
			var lst = slider.noUiSlider.get();
			if (!$.isArray(lst)) { return; }
			// https://davidwalsh.name/remove-item-array-javascript
			else { lst.splice(Math.floor(lst.length/2), 1); }
			var opts = master;
			opts.start = lst;
			var ts; (ts = []).length = lst.length + 1; ts.fill(true); opts.connect = ts;
			slider.noUiSlider.destroy();
			noUiSlider.create(slider, opts);
			counts[i] = lst.length + 1;
			setConnects();
			console.log(counts);
		});
	});

	function myfix(lst) { return lst.map(function(x) { return parseFloat(Math.floor(x)) + parseFloat(Math.floor(((x%1)+.25)/.5))*.5; }); }
	function setConnects() {
		$(".noUi-connect").each(function(i) { $(this).click(function() {
			var c = 0; var sum = 0;
			while (sum < i + 1) { sum += counts[c]; c += 1; }
			console.log(c - 1);
		});});
	}
	setConnects();

	// $(".sched-slider").each(function() { noUiSlider.create(this, monopts); });

	// noUiSlider.create(sunslider, monopts);
	// noUiSlider.create(monslider)
	// monlist = s.noUiSlider.get();
	// $("#mon-add").click(function() {
	// 	monlist = s.noUiSlider.get().map(
	// 		function(item) {
	// 			return parseFloat(item);
	// 		}
	// 	);
	// 	monlist = $.merge([0], monlist);
	// 	console.log(monlist);
	// 	s.noUiSlider.destroy();
	// 	monopts.start = monlist;
	// 	noUiSlider.create(s, monopts);
	// 	console.log(monopts);
	// });
	
});
