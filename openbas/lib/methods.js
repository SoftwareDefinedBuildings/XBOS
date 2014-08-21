common_metadata = function(o) {
    /*
     * Given a System object (from HVAC, Lighting or Monitoring) with a .timeseries attribute,
     * finds the metadata common for this source
     */
    return intersect_json(_.values(o.timeseries))
};

intersect_json = function(o){
  /*
   * Finds common metadata recursively. Takes as an argument
   * a list of objects
   */
  o = _.compact(o);
  var ks = []
  _.each(o, function(el){
    if (!el) { return; }
    ks.push(_.keys(el))
  });
  ks = _.uniq(_.flatten(ks))
  var r = {}
  _.each(ks, function(k){
    vs = _.uniq(_.pluck(o, k))
    if (typeof vs[0] == "object") {
      var r_rec = intersect_json(vs)
      if (!$.isEmptyObject(r_rec)) {
        r[k] = r_rec
      }
    } else if (vs.length == 1){
      r[k] = vs[0]
    }
  });
  return r
};

get_source_path = function(path) {
  return path.slice(0,path.lastIndexOf('/'));
};

fix_path = function(path) {
  return path.replace(/\//g,'_');
};

/*
 * need a method that for a given metadata key, gives
 * a list of possible options. This should probably be done using
 *
 * select distinct metadata/tag;
 *
 * and looking at output, but that's asynchronous, so we can't do it UNLESS
 * we have it as a callback or some weird shit like that
 */

get_autocomplete_options = function(metadatakey, callback) {
    var data = [];

    var query = 'select distinct Metadata/'+metadatakey;
    Meteor.call('query', query, function(err, val) {
        if (err) {
          console.log(err);
          callback(data);
        }
        console.log('autocomplete options for',metadatakey,':',val);
        callback(val);
    });
};

if (Meteor.isServer) {
  Meteor.methods({
    // in the client:
    // Meteor.call('method_name', param, param, function(err, data){ ... });

    query: function(q){
      var url = Meteor.settings.archiverUrl + "/api/query";
      console.log("Query:",q);
      var r = HTTP.call("POST", url, {content: q});
      return EJSON.parse(r.content);
    },

    latest: function(restrict, n){
      var q = "select data before now limit " + n + " where " + restrict;
      var url = Meteor.settings.archiverUrl + "/api/query";
      console.log(restrict);
      console.log(url);
      var r = HTTP.call("POST", url, {content: q});
      return EJSON.parse(r.content);
    },

    tags: function(uuid){
      this.unblock();
      var url = Meteor.settings.archiverUrl + "/api/tags/uuid/"+ uuid;
      var r = HTTP.call("GET", url);
      res = EJSON.parse(r.content);
      if ('Actuator' in res[0] && 'Values' in res[0].Actuator) {
        var x = res[0].Actuator.Values.replace(/'/g, '"');
        res[0].Actuator.Values = EJSON.parse(x);
      }
      return res;
    },

    actuate: function(port, path, value){
      this.unblock();
      var url = "http://localhost:" + port + "/data"+path+"?state="+value;
      var r = HTTP.call("PUT", url);
      HTTP.call("GET", url);
      return EJSON.parse(r.content);
    },

    updatetags: function(restrict, tags) {
      /*
       * restrict: string 'where' clause telling sMAP which timeseries are to be updated
       * tags: list of [tag, value] arrays to be set
       */
      var url = Meteor.settings.archiverUrl + "/api/query?key=" + Meteor.settings.apikey;
      console.log(url);
      var results = [];
      _.each(tags, function(val, idx) {
        var tag = val[0];
        var value = val[1];
        var query = "set " + tag + " = '"+value+"' where " + restrict;
        console.log(query);
        var r = HTTP.call("POST", url, {content: query});
        console.log(r);
        results.push(EJSON.parse(r.content));
      });
      return results;

    },
  });
}

Meteor.methods({
  /*
   * Removes everything after the last '/' in a path and returns
   */
  get_source_path:  function(path) {
    return path.slice(0,path.lastIndexOf('/'));
  },

  /*
   * Returns value after last '/' in path
   */
  get_endpoint: function(path) {
    var p = path.split('/');
    return p[p.length-1];
  },

});
