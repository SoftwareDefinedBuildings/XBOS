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
      var url = Meteor.settings.archiverUrl + "/api/query";
      var r = HTTP.call("POST", url, {content: q});
      return EJSON.parse(r.content);
  },

  latest: function(restrict, n){
      var q = "select data before now limit " + n + " where " + restrict;
      var url = Meteor.settings.archiverUrl + "/api/query";
      var r = HTTP.call("POST", url, {content: q});
      return EJSON.parse(r.content);
  },

  tags: function(uuid){
    if (Meteor.isServer) {
      this.unblock();
      var url = Meteor.settings.archiverUrl + "/api/tags/uuid/"+ uuid;
      var r = HTTP.call("GET", url);
      res = EJSON.parse(r.content);
      if ('Actuator' in res[0] && 'Values' in res[0].Actuator) {
        var x = res[0].Actuator.Values.replace(/'/g, '"');
        res[0].Actuator.Values = EJSON.parse(x);
      }
      return res;
    }
  },

  actuate: function(port, path, value){
    if (Meteor.isServer) {
      this.unblock();
      var url = "http://localhost:" + port + "/data"+path+"?state="+value;
      console.log("URL",url)
      var r = HTTP.call("PUT", url);
      return EJSON.parse(r.content);
    }
  },

});
