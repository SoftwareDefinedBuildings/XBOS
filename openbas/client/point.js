Template.points.rendered = function(){
  var rows = $(".point");
  _.each(rows, function(row){
    var uuid = $(row).data('uuid');     
    var restrict = 'uuid="' + uuid + '"';
    var elementId = '#trend-' + uuid; 
    var width = 150;
    var height = 40;
    var N = width;
    var q = "select data in (now -8h, now) where " + restrict;
    Meteor.call("query", q, function(err, res){
      if (res[0] != undefined){
        var mydata = jsonify(res[0].Readings);
        sparkline(elementId, mydata, width, height, "last 8 hours");
      }
    });
  });
};
