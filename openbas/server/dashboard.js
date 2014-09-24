if (Meteor.isServer) {
    Meteor.methods({
        querysystem: function() {

          var get_source_path = function(path) { return Meteor.call('get_source_path', path); }
          var get_endpoint = function(path) { return Meteor.call('get_endpoint', path); }

          // query all HVAC system points at our current site
          _.each(['HVAC','Lighting','Monitoring', 'GeneralControl'], function(system, index) {
            var query = "select * where Metadata/Site = '" + Meteor.settings.public.site + "'";
            query += " and Metadata/System = '" + system + "'";
            if (system == 'HVAC') {
              query += " and not Metadata/HVACZone = ''";
            } else if (system == 'Lighting') {
              query += " and not Metadata/LightingZone = ''";
            } else if (system == 'GeneralControl') {
              query += " and not Metadata/Room = ''";
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
                var driver = my_ts[0].Metadata.Driver;
                var roomname = my_ts[0].Metadata.Room;
                console.log(path)
                if (system == 'HVAC') {
                  var zonename = my_ts[0].Metadata.HVACZone;
                } else if (system == 'Lighting') {
                  var zonename = my_ts[0].Metadata.LightingZone;
                  var groupname = my_ts[0].Metadata.Group;
                } else if (system == 'Monitoring') {
                  var lightzonename = my_ts[0].Metadata.LightingZone;
                  var hvaczonename = my_ts[0].Metadata.HVACZone || my_ts[0].Metadata.Hvaczone;
                } else if (system == 'GeneralControl') {
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
                    'hvaczone': zonename, 
                    'lightingzone': '',
                    'room': roomname, 
                    'device': device,
                    'model': model,
                    'driver': driver,
                    'configured': true,
                    'timeseries': record
                  });
                } else if (system == 'Lighting') {
                  Lighting.upsert({'path': path}, {
                    'path': path, 
                    'group': groupname, 
                    'lightingzone': zonename, 
                    'hvaczone': '',
                    'room': roomname, 
                    'role': role, 
                    'device': device,
                    'model': model,
                    'driver': driver,
                    'configured': true,
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
                    'driver': driver,
                    'configured': true,
                    'timeseries': record
                  });
                } else if (system == 'GeneralControl') {
                  GeneralControl.upsert({'path': path}, {
                    'path': path, 
                    'room': roomname, 
                    'lightingzone': lightzonename, 
                    'hvaczone': hvaczonename, 
                    'device': device,
                    'model': model,
                    'driver': driver,
                    'configured': true,
                    'timeseries': record
                  });
                }
              });
            });
          }); 

        }, 

        savemetadata: function(objid, update) {
            /*
             * Given an object ID, first try to update an existing object. To do this,
             * we search the HVAC, Lighting and Monitoring collections. If we find a record
             * with this ID, we update it and save
             *
             * If we don't find it, then that means this is an object in the Unconfigured collection.
             * We remove it from that collection, and then look at update['system'] to figure
             * out which collection it belongs in. We add any and all extra metadata and commit
             * it to that collection
             *
             * Regardless of what happens above, we have to push the updates to the archiver
             * and then to the source of the configuration file.
             */
            console.log("savemetadata called with", objid, update);
            var found = false;
            var tags = [['Metadata/Site',Site.findOne({'_id':'Site'})['Site']],['Metadata/Building',Site.findOne({'_id':'Building'})['Building']]];
            var path = '';
            var goalsystem = update['System']
            _.each([HVAC, Lighting, Monitoring, GeneralControl], function(system, idx) {
                if (found) { return; } // if we've found, no need to check other collections
                var record = system.findOne({'_id': objid});
                if (record) {
                    found = true;
                    delete update['system']
                    delete update['_id']
                    system.update(objid, {$set: update});
                    path = record.path;
                }
            });

            // here, we know that we haven't found the object, so it must be in the Unconfigured collection
            if (!found) {
              console.log("got this far!");
              update['configured'] = true;
              var record = Unconfigured.findOne({'_id': objid});
              Unconfigured.remove({'_id': record['_id']});
              record = Unconfigured.findOne({'_id': objid});
              console.log("unconf record", record);
              path = objid;
              
              var allpoints = Points.find({}).fetch();
              var mypoints = _.pluck(_.filter(allpoints, function(o) { return get_source_path(o.Path) == path; }), 'uuid');
              console.log(mypoints);
              _.each(mypoints, function(val, idx) {
                Points.update({'uuid': val},{$set: {'configured': true}})
              });
            }

            // prepare data for committing to archiver
            _.each(update, function(v, k) {
                if (v == null) { // do not erase data. If null, skipit
                    return;
                }
                tags.push(['Metadata/'+k, v]);
            });

            // here, update archiver with tags
            res = Meteor.call('updatetags', 'Path like "'+path+'/%"', tags);
            Meteor.call('querysystem');
        }
    }); 
} 
