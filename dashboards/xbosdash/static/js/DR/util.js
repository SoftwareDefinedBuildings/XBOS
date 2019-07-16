let c = ["#66bb6a", "#8d6e63", "#EF5350", "#42A5F5", "#000000", "#e6194b", "#008080", "#911eb4", "#0082c8"];
let lines = ["Solid", "Solid", "ShortDash", "ShortDash", "Solid", "ShortDash", "Dot", "ShortDot", "Solid"];
let ws = [4, 2, 2, 2, 2, 2, 2, 2, 2];
let CLEN = 9;

function getTime(et, x) { return toDate(et).toString().split(" ")[4].slice(0, x); }

function toDate(et) {
    var d = new Date(0);
    d.setUTCSeconds(et);
    return d;
}

// http://www.jacklmoore.com/notes/rounding-in-javascript/
function round(val, dec) { return Number(Math.round(val+'e'+dec)+'e-'+dec); }

function processResp(j) {
    var toRet = [];
    for (var z in j) {
        var lst = [];
        var prevKeys = [];
        var st;
        for (var s in j[z]) {
            var toAdd = new Object();
            toAdd.id = clean(z).toLowerCase() + " " + s;
            toAdd.name = toAdd.id;
            if (s == "state") {
                toAdd.data = j[z][s];
                st = toAdd;
            } else {
                var ret = makeData(j[z][s], toAdd.id);
                toAdd.data = ret[0];
                var k = ret[1];
                if (k.length > prevKeys.length) { prevKeys = k; }
                lst.push(toAdd);
            }
        }
        var cleaned = clean(z); lst[0].name = cleaned; lst[0].id = cleaned;
        st.data = makeState(st.data, prevKeys, st.id);
        st.yAxis = 1;
        st.step = "center";
        lst.push(st);
        var i; for (i = 0; i < lst.length; i += 1) {
            lst[i].dashStyle = lines[i];
            lst[i].color = c[i % CLEN];
            lst[i].lineWidth = ws[i];
        }
        // console.log(lst);
        if (!toRet.length) { lst[0].visible = true; }
        else { lst[0].visible = false; }
        $.merge(toRet, lst);
    }
    // console.log(toRet);
    return toRet;
}

function processPower(j) {
    var toRet = [];
    for (var z in j) {
        console.log(z);
    }
}

// make multiple series maybe
function makeState(j, l, n) {
    var toRet = [];
    var prev = null;
    var col = null;
    var r;
    for (var k in l) {
        var toAdd = new Object();
        toAdd.name = getTime(l[k]/1000, 5);
        toAdd.id = n + " " + toAdd.name;
        if (l[k] in j) {
            r = stateClean(j[l[k]]);
            prev = round(r[0], 2);
            // col = r[2];
        }
        // toAdd.color = col;
        toAdd.y = prev;
        toAdd.id += " " + r[1];
        toRet.push(toAdd);
    }
    return toRet;
}

function stateClean(x) {
    if (x == "off") { return [-2, "off", "#424242"]; }
    if (x == "heat stage 1") { return [2, "he1", "#e57373"]; }
    if (x == "heat stage 2") { return [0, "he2", "#e53935"]; }
    if (x == "cool stage 1") { return [0, "co1", "#64b5f6"]; }
    if (x == "cool stage 2") { return [0, "co2", "#1976d2"]; }
}

function makeData(j, n) {
    var toRet = [];
    var ret = [];
    for (var k in j) {
        ret.push(k);
        var toAdd = new Object();
        toAdd.name = getTime(k/1000, 5);
        toAdd.id = n + " " + toAdd.name;
        toAdd.y = round(j[k], 2);
        toRet.push(toAdd);
    }
    return [toRet, ret];
}

function clean(s, shorten=false, amt=null) {
    s = s.replace("-", "_");
    s = s.split("_");
    if (shorten && amt) { for (var i in s) { if (s[i].length > amt) { s[i] = s[i].slice(0, amt); }}}
    for (var i in s) { s[i] = s[i].charAt(0).toUpperCase() + s[i].slice(1).toLowerCase(); }
    s = s.join("");
    s = s.replace("Zone", "").replace("ZONE", "").replace("zone", "");
    s = s.replace("HVAC", "").replace("Hvac", "").replace("hvac", "");
    return s;
}

function pointFormatter() {
    // if ("state" in this) {
        // last 3 chars
        // return this.id.toString().reverse().slice(3).reverse();
    // }
    // if (state in $(this).id) { return "sdf"; }
    // else {
    return "<span style='font-size: 14px;'>" + this.id.split(" ")[1] + this.y + "<br/>";
    // }
}


