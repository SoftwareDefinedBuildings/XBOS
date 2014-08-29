jsonify = function (readings){
  return _.map(readings, function(r){
    var o = {};
    o.time = r[0];
    o.value = r[1];
    return o;
  });
};

sparkline = function(elemId, data, width, height, display_range) {
  var x = d3.scale.linear().range([0, width]);
  var y = d3.scale.linear().range([height, 0]);
  var line = d3.svg.line()
               .interpolate("basis")
               .x(function(d) { return x(d.time); })
               .y(function(d) { return y(d.value); });
  x.domain(d3.extent(data, function(d) { return d.time; }));
  var yextents = d3.extent(data, function(d) { return d.value; });
  y.domain(yextents);

  var svg = d3.select(elemId)
    .append('svg')
    .attr('width', width)
    .attr('height', height)
    .append('path')
    .datum(data)
    .attr('class', 'sparkline')
    .attr('d', line);

  if (display_range){
    var extents_label = "[<span class='sparkline-min'>" + yextents[0].toFixed(2) + "</span>,";
    extents_label += "<span class='sparkline-max'>" + yextents[1].toFixed(2) + "</span>]";
    d3.select(elemId)
      .html(extents_label)
  }
};

common_metadata = function(o) {
    /*
     * Given a System object (from HVAC, Lighting or Monitoring) with a .timeseries attribute,
     * finds the metadata common for this source
     */
    if (!o.timeseries) {
        var ret = {};
        _.each(o, function(val, key) {
            ret[key.toProperCase()] = val;
        });
        ret['configured'] = false;
        return {'Metadata': ret};
    }
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
 * finds a meteor record in the HVAC, Lighting or Monitoring collections
 * and returns both the record and which collection it found it in
 */
find_by_id = function(_id) {
    var predicate = {'_id': _id};
    var record = null;
    record = HVAC.findOne(predicate);
    if (record) {
        return [record, 'HVAC'];
    }
    record = Lighting.findOne(predicate);
    if (record) {
        return [record, 'Lighting'];
    }
    record = Monitoring.findOne(predicate);
    if (record) {
        return [record, 'Monitoring'];
    }
    record = Unconfigured.findOne(predicate);
    return [record, "Unconfigured"];
};

find_by_path = function(path) {
    var predicate = {'path': path};
    var record = null;
    record = HVAC.findOne(predicate);
    if (record) {
        return [record, 'HVAC'];
    }
    record = Lighting.findOne(predicate);
    if (record) {
        return [record, 'Lighting'];
    }
    record = Monitoring.findOne(predicate);
    if (record) {
        return [record, 'Monitoring'];
    }
    return [null, null]
};

/*
 * need a method that for a given metadata key, gives
 * a list of possible options. This should probably be done using
 *
 * select distinct metadata/tag;
 *
 * Takes two arguments: metadatakey, which is the name of <key> in Metadata/<key>,
 * and a callback function which takes the results of the query as an argument
 */
get_autocomplete_options = function(metadatakey, callback) {
    var data = [];

    if (metadatakey == 'Room') {
        data = _.pluck(Rooms.find().fetch(), 'RoomNumber');
    }

    if (metadatakey == 'System') {
        data = ['Monitoring','HVAC','Lighting','GeneralControl'];
    }

    if (metadatakey == 'Role') {
        data = ['Building Lighting','Task Lighting','Building HVAC'];
    }

    var query = 'select distinct Metadata/'+metadatakey+' where Metadata/Site="'+Meteor.settings.public.site+'"';
    Meteor.call('query', query, function(err, val) {
        if (err) {
          console.log('err',err);
          callback(data);
        }
        console.log('autocomplete options for',metadatakey,':',val);
        val.push.apply(val, data)
        callback(_.uniq(val));
    });
};

get_last_seen = function(path) {
    var allpoints = Points.find({}).fetch();
    var mypoints = _.filter(allpoints, function(o) { return get_source_path(o.Path) == path; });
    var maxtimestamp = _.max(_.pluck(mypoints, 'time'));
    return moment(new Date(maxtimestamp * 1000));
};

if (Meteor.isServer) {
  Meteor.methods({
    // in the client:
    // Meteor.call('method_name', param, param, function(err, data){ ... });

    query: function(q){
      this.unblock();
      var url = Meteor.settings.archiverUrl + "/api/query?key="+Meteor.settings.apikey;
      console.log("Query:",q);
      var r = HTTP.call("POST", url, {content: q});
      return EJSON.parse(r.content);
    },

    latest: function(restrict, n){
      this.unblock();
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
      this.unblock();
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
