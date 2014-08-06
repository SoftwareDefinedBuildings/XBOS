Points = new Meteor.Collection("points");
HVAC = new Meteor.Collection("hvac");
Lighting = new Meteor.Collection("lighting");

if (Meteor.isServer) {
  Meteor.methods({
    querysystem: function() {
      if (Meteor.isServer) {
        console.log('called!')

      var get_source_path = function(path) { return Meteor.call('get_source_path', path); }
      var get_endpoint = function(path) { return Meteor.call('get_endpoint', path); }
      // query all HVAC system points at our current site
      _.each(['HVAC','Lighting'], function(system, index) {
        var query = "select * where Metadata/Site = '" + Meteor.settings.public.site + "'";
        query += " and Metadata/System = '"+system+"'";
        if (system == 'HVAC') {
          query += " and not Metadata/HVACZone = ''";
        } else if (system == 'Lighting') {
          query += " and not Metadata/LightingZone = ''";
        }

        Meteor.call('query', query, function(err, res) {
          // quick error checking
          if (err) {
            console.log("Error running query:",query, err);
            return
          }
          if (!res) {
            console.log("No results found for",query);
            return
          }
          console.log(res);
          
          /* 
           * Need to find unique paths. Unfortunately, we have full timeseries paths. Need
           * to lop off the last '/'-delimited segment and then take the unique set
           */
          var source_paths = _.map(_.pluck(res, 'Path'), get_source_path);
          var unique_paths = _.uniq(source_paths);
          console.log('unique paths', unique_paths);

          /*
           * for each unique_path, we add it to the system collection as a key. The value is
           * an object that maps each aspect (e.g. temp, temp_heat, etc) to its uuid. This
           * will facilitate lookups in the Points collection
           */
          _.each(unique_paths, function(src_path, idx) {
            // get timeseries objects for this unique_path
            var my_ts = _.filter(res, function(o) { return get_source_path(o.Path) == src_path; });
            if (system == 'HVAC') {
              var zonename = my_ts[0].Metadata.HVACZone;
            } else if (system == 'Lighting') {
              var zonename = my_ts[0].Metadata.LightingZone;
              var groupname = my_ts[0].Metadata.Group;
            }
            // the record we will insert
            var record = {};
            _.each(my_ts, function(val, idx) {
              var endpoint = get_endpoint(val.Path);
              record[endpoint] = val
            });

            // insert into database
              if (system == 'HVAC') {
                HVAC.upsert({'zone': zonename}, {'zone': zonename, 'timeseries': record});
              } else if (system == 'Lighting') {
                Lighting.upsert({'group': groupname}, {'group': groupname, 'zone': zonename, 'timeseries': record});
              }

          });

        });
      });
      }
    },
  })
}

