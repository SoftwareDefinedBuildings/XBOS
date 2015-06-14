// For a path e.g. /devices/thermostat0/heat_set_point, removes everything
// after the last slash (including the slash), e.g. /devices/thermostat0
// This is a legacy function from OpenBAS v1, and device grouping should
// instead be done by grouping timeseries by their Metadata/DeviceID tag
var get_source_path = function(path) {
  return path.slice(0,path.lastIndexOf('/'));
}

// This is the corollary of get_source_path. Given a path e.g.
// /devices/thermostat0/heat_set_point, this will return the last
// string after the last '/'
var get_timeseries = function(path) {
   return path.slice(path.lastIndexOf('/')+1);  // add one to skip the leading '/'
}

// For republish mechanisms, we will often get arrays that look like
// [[1425582802,75],[1425582803,75]]. This fetches the most recent reading
// and returns it
var get_latest_reading = function(reading) {
    if (reading.length == 0) {
        return null;
    }
    return reading[reading.length-1][1];
}

// Like get_latest_reading, but returns the timestamp
var get_latest_timestamp = function(reading) {
    if (reading.length == 0) {
        return null;
    }
    return reading[reading.length-1][0];
}

// In sMAP, devices are represented as an array of timeseries that all
// share the same Metadata/DeviceID. This is a convenience method that
// re-presents this array of timeseries as an object
//
// Input like
//
// [{
//   'Path': '/devices/thermostat0/temp_heat',
//   'Metadata/XYZ': 123,
//   ...
//  },
//  {
//   'Path': '/devices/thermostat0/temp_cool',
//   'Metadata/ABC': 456,
//   ...
//  },
//  ...
// ]
//
// will have output like
//
// {
//  'temp_heat': {'Path': '/devices/thermostat0/temp_heat',
//                'Metadata/XYZ': 123,
//                etc...}
//  'temp_cool': {'Path': '/devices/ethermostat0/temp_cool',
//                'Metadata/ABC': 456,
//                etc...}
//  etc...
// }
//
// This ALSO pull out all the common/shared Metadata and Properties and puts
// them in special attributes _Metadata and _Properties
var get_device_view = function(timeseries) {
    ret = {};
    _.each(timeseries, function(elem, idx, list) {
        if (_.has(elem,'Path')) {
            ret[get_timeseries(elem.Path)] = elem;
        }
    });
    ret['_Metadata'] = intersect_json(_.pluck(timeseries,'Metadata')); // common metadata
    ret['_Properties'] = intersect_json(_.pluck(timeseries,'Properties')); // common metadata
    return ret;
}

var intersect_json = function(o){
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

// convenience method for running AJAX POST
var run_query = function(q, succ, err) {
    $.ajax({
        url: queryURL,
        datatype: 'json',
        type: 'POST',
        data: q,
        success: succ.bind(this),
        error: err.bind(this)
    });
};

var LOOKUP = {
    "Heating Setpoint": "Metadata/Point/Type = 'Setpoint' and Metadata/Point/Setpoint = 'Heating'",
    "Cooling Setpoint": "Metadata/Point/Type = 'Setpoint' and Metadata/Point/Setpoint = 'Cooling'",
    "Temperature": "Metadata/Point/Type = 'Sensor' and Metadata/Point/Sensor = 'Temperature'",
    "Humidity": "Metadata/Point/Type = 'Sensor' and Metadata/Point/Sensor = 'Humidity'",
    "Brightness": "Metadata/Point/Type = 'Command' and Metadata/Point/Command = 'Brightness'",
    "Hue": "Metadata/Point/Type = 'Command' and Metadata/Point/Command = 'Hue'",
    "Illumination": "Metadata/Point/Type = 'Sensor' and Metadata/Point/Sensor = 'Illumination'",
    "On": "Metadata/Point/Type = 'Command' and Metadata/Point/Command = 'On'",
};
