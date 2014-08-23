function parsePixelsToInt(q) {
    return parseFloat(q.slice(0, q.length - 2));
}
instances = [];
if (Meteor.isClient) {
    var localtest = false;
    Template.plot.plot_data = [
        {
            tagsURL: localtest ? 'http://localhost:7856' : (Meteor.settings.public.archiverUrl + "/api/query?"),
            dataURLStart: localtest ? 'http://localhost:7856/data/uuid' : 'http://archiver.cal-sdb.org:9000/data/uuid/',
            bracketURL: "http://archiver.cal-sdb.org:9000/q/bracket",
            width: function () {
                    var $parent = $(instances[instances.length-1].find('.chartContainer')) /* hack */
                    var width = $parent.css("width");
                    var leftpadding = $parent.css("padding-left");
                    var rightpadding = $parent.css("padding-right");
                    return parsePixelsToInt(width) - parsePixelsToInt(leftpadding) - parsePixelsToInt(rightpadding);
                }/*,
            hide_main_title: true,
            hide_graph_title: true,
            hide_settings_title: true*/
        }, 
        function (inst) 
        { 
            instances.push(inst);
        },
        window.location.search.length == 0 ? '' : window.location.search.slice(1)];
}
