if (Meteor.isServer) {
  Meteor.methods({
    querysystem: function() {

      var get_source_path = function(path) { return Meteor.call('get_source_path', path); }
      var get_endpoint = function(path) { return Meteor.call('get_endpoint', path); }

      // query all HVAC system points at our current site
      _.each(['HVAC','Lighting','Monitoring'], function(system, index) {
        var query = "select * where Metadata/Site = '" + Meteor.settings.public.site + "'";
        query += " and Metadata/System = '"+system+"'";
        if (system == 'HVAC') {
          query += " and not Metadata/HVACZone = ''";
        } else if (system == 'Lighting') {
          query += " and not Metadata/LightingZone = ''";
          //query += " and Metadata/Role = 'Building Lighting'";
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
          
          /* 
           * Need to find unique paths. Unfortunately, we have full timeseries paths. Need
           * to lop off the last '/'-delimited segment and then take the unique set
           */
          var source_paths = _.map(_.pluck(res, 'Path'), get_source_path);
          var unique_paths = _.uniq(source_paths);

          /*
           * for each unique_path, we add it to the system collection as a key. The value is
           * an object that maps each aspect (e.g. temp, temp_heat, etc) to its uuid. This
           * will facilitate lookups in the Points collection
           */
          _.each(unique_paths, function(src_path, idx) {
            // get timeseries objects for this unique_path
            var my_ts = _.filter(res, function(o) { return get_source_path(o.Path) == src_path; });
            var path = get_source_path(my_ts[0].Path);
            var role = my_ts[0].Metadata.Role;
            var device = my_ts[0].Metadata.Device;
            var model = my_ts[0].Metadata.Model;
            console.log(path)
            if (system == 'HVAC') {
              var zonename = my_ts[0].Metadata.HVACZone;
            } else if (system == 'Lighting') {
              var zonename = my_ts[0].Metadata.LightingZone;
              var groupname = my_ts[0].Metadata.Group;
            } else if (system == 'Monitoring') {
              var roomname = my_ts[0].Metadata.Room;
              var lightzonename = my_ts[0].Metadata.LightingZone;
              var hvaczonename = my_ts[0].Metadata.HVACZone || my_ts[0].Metadata.Hvaczone;
            }
            // the record we will insert
            var record = {};
            _.each(my_ts, function(val, idx) {
              var endpoint = get_endpoint(val.Path);
              record[endpoint] = val
            });

            // insert into database
            if (system == 'HVAC') {
              HVAC.upsert({'path': path}, {
                'path': path, 
                'zone': zonename, 
                'device': device,
                'model': model,
                'timeseries': record
              });
            } else if (system == 'Lighting') {
              Lighting.upsert({'path': path}, {
                'path': path, 
                'group': groupname, 
                'zone': zonename, 
                'role': role, 
                'device': device,
                'model': model,
                'timeseries': record
              });
            } else if (system == 'Monitoring') {
              Monitoring.upsert({'path': path}, {
                'path': path, 
                'room': roomname, 
                'lightingzone': lightzonename, 
                'hvaczone': hvaczonename, 
                'device': device,
                'model': model,
                'timeseries': record
              });
            }

          });
        });
      }); 

    }, 
  }); 
} 
