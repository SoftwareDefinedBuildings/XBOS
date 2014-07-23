Meteor.methods({
  // in the client: 
  // Meteor.call('method_name', param, param, function(err, data){ ... });

  foo: function(){
    return 'bar';
  },

  bar: function(a, b){
    return a + b;
  },

  query: function(q){
      var url = Meteor.settings.archiverUrl + "/api/query"
      var r = HTTP.call("POST", url, {content: q})
      return EJSON.parse(r.content);
  },

  latest: function(restrict, n){
      var q = "select data before now limit " + n + " where " + restrict;
      var url = Meteor.settings.archiverUrl + "/api/query";
      var r = HTTP.call("POST", url, {content: q});
      return EJSON.parse(r.content);
  },

});
