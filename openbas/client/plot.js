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
        }, 
        function (inst) 
        { 
            instances.push(inst);
            s3ui.default_cb1(inst);
        },
        s3ui.default_cb2];
}
