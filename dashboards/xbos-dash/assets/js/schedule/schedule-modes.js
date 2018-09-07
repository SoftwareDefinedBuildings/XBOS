$(document).ready(function() {
	M.AutoInit();
	var mode = false;
	function editModes(c=true) {
		var x = $("#mode-edit");
		x.removeClass("scale-in");
		x.addClass("scale-out");
		mode = !mode;
		if (mode) { $("#mode-radios").show(); var s = "save"; } else { $("#mode-radios").hide(); var s = "edit"; }
		setTimeout(function() {
			x.html("<i class='large material-icons'>" + s + "</i>");
			x.removeClass("scale-out");
			x.addClass("scale-in");
			clearTimeout(this);
		}, 250);
		if (c && edit) { edit = true; schedClick(false); }
	} $("#mode-edit").click(editModes);

	function getEdit() { if (mode) { return "save"; } else { return "edit"; }}

	var modenum = 3;
	var colors = ["#3B7EA1", "#FDB515", "#cab2d6", "#fccde5", "#fb9a99", "#b2df8a"];
	function addMode() {
		$("#mode-btn-div").remove();
		$("#mode-stq").remove();
		$("#mode-div").append("<div style='background-color:" + colors[modenum] + ";' class='col s1-7 z-depth-1 mode-card'><input id='mode" + modenum + "' type='text' maxlength='10' placeholder='Mode Name' class='my-input mode-title' /><div class='setpnt-div'><input class='red lighten-2' value=55 type='number' max='72' min='35' /><input class='blue lighten-2' value=85 type='number' max='90' min='74' /></div><div class='switch'><label><input class='ogswitch' type='checkbox'><span class='lever'></span></label></div></div>");
		$("#mode-radios").append("<div class='col s1-7'><label><input class='with-gap' name='group1' type='radio' /><span style='margin-left: 5px;'></span></label></div>");
		modenum += 1;
		if (modenum != 6) {
			$("#mode-div").append("<div id='mode-btn-div' class='col stq'><a id='mode-btn' class='btn btn-floating waves-effect waves-light'><i class='large material-icons'>add</i></a><div class='row'></div><div class='row'></div><a id='mode-edit' class='btn btn-floating waves-effect waves-light blue scale-transition'><i class='large material-icons'>" + getEdit() + "</i></a></div>");
			$("#mode-radios").append("<div id='mode-stq' class='col stq'></div>");
		}
		$("#mode-edit").click(editModes);
		$("#mode-btn").click(addMode);
		checkModes();
	}

	$("#mode-btn").click(addMode);

	function checkModes() {
		if (modenum > 3) {
			$("#first-mode").css("margin-left", "0");
			$("#first-radio").css("margin-left", "0");
		} else {
			$("#first-mode").css("margin-left", "auto");
			$("#first-radio").css("margin-left", "auto");
		}
	}

});
