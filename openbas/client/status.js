if (Meteor.isClient) {

  Session.set('selectedhvaczone', null);
  Session.set('selectedlightingzone', null);
  hvaczones = function() {
    return _.uniq( _.filter( _.pluck(Rooms.find().fetch(), 'HVACZone'), function(o) { return o != null; }));
  };

  roomsForHVACZone = function(zone) {
    if (!zone) {
      return []
    }
    return _.pluck(Rooms.find({'HVACZone':zone}).fetch(), 'RoomNumber');
  };

  //TODO: where do we pull lighting zones from? there can be multiple in a room? What defines a lighting zone?
  lightingzones = function() {
    return _.uniq( _.filter( _.pluck(Rooms.find().fetch(), 'LightingZone'), function(o) { return o != null; }));
  };

  roomsForLightingZone = function(zone) {
    if (!zone) {
      return []
    }
    return _.pluck(Rooms.find({'LightingZone':zone}).fetch(), 'RoomNumber');
  };

  hvaczoneByID = function(_id) {
      var predicate = {'_id': _id};
      record = HVAC.findOne(predicate) || Lighting.findOne(predicate) || Monitoring.findOne(predicate);
      if (record) {
        return record.hvaczone;
      }
      return null
  };

  lightingzonebyId = function(_id) {
      var predicate = {'_id': _id};
      record = HVAC.findOne(predicate) || Lighting.findOne(predicate) || Monitoring.findOne(predicate);
      if (record) {
        return record.lightingzone;
      }
      return null
  };
  
  UI.registerHelper('fixPath', function(p) {
    return p.replace(/\//g,'_');
  });

  UI.registerHelper('hvaczones', function() {
    return hvaczones();
  });

  UI.registerHelper('lightingzones', function() {
    return lightingzones();
  });

  /*
   */
  Template.status.created = function() {
    Points.find().observe({
    added: function(doc) {
        if (doc.configured) {
            return
        }
        console.log('unconfigured doc', doc);
        var src_path = get_source_path(doc.Path);
        if (!Unconfigured.findOne({'_id': src_path})) {
          Meteor.call('query', "select * where Path = '"+doc.Path+"'", function(err, res) {
              if (err) {console.log("error:", err); return; }
              if (!res) {console.log("no results"); return; }
              console.log("got result", res);
              var rec = {'device': res[0].Metadata.Device,
                        'uuid': doc.uuid,
                        'model': res[0].Metadata.Model,
                        'driver': res[0].Metadata.Driver,
                        'path': src_path,
                        'configured': false,
                        '_id': src_path};
              console.log('inserting', rec);
              Unconfigured.upsert({'_id': src_path}, rec);
          });
        }
    }
    });
  };

  Template.status.sources = function() {
    /*
     * Grabs all the HVAC, Lighting and Monitoring points. These
     * have been configured, so we can read their metadata. Thanks
     * to the 'querysystem' function, thse are pre-aggregated by
     * their driver path instead of the individual timeseries
     */
    var sources = []
    sources.push.apply(sources, Lighting.find().fetch())
    sources.push.apply(sources, HVAC.find().fetch())
    sources.push.apply(sources, Monitoring.find().fetch())
    return sources;
  };

  /*
   * Inside the Unconfigured collection, we have the timeseries endpoints.
   * We need to group them by their source path, and then retrieve their collective
   * metadata from the archiver
   *
   * Need to add a key to the meteor collections so that we can tell if something
   * has been configured or not. This should take care of the problem where 
   * everything is considered 'unconfigured' upon setup.
   */

  Template.status.unconfigured = function() {
    return Unconfigured.find().fetch();
  };

  Template.device.color = function() {
    if (this.configured != null && !this.configured) {
        return 'warning';
    }
    return '';
  };
  Template.device.driverPath = function() {
    /*
     * From the driver module path (e.g. smap.drivers.lights.VirtualLightDriver),
     * we generate the URL to the code of the driver
     */
    var baseurl = "https://github.com/SoftwareDefinedBuildings/smap/tree/unitoftime/python";
    var components = this.driver.split('.');
    _.each(components, function(val, idx) {
      baseurl += '/' + val
    });
    baseurl += '.py';
    return baseurl;
  };

  Template.configuration.events({
    'click .btn-info': function(e) {
        var path = this.path;
        var fixedpath = this.path.replace(/\//g,'_');
    },

    'change .hvaczones': function(e, template) {
        Session.set('selectedhvaczone', template.find('.hvaczones').value);
    },

    'change .lightingzones': function(e, template) {
        Session.set('selectedlightingzone', template.find('.lightingzones').value);
    },

    //'click .save': function(e, template) {
    //  var path = this.path;
    //  console.log('form save',template, e);
    //  var hvaczone = template.find('.hvaczones').value || null;
    //  var lightingzone = template.find('.lightingzones').value || null;
    //  var room = template.find('.rooms').value || null;
    //  var system = null;
    //  if (this.configured == null || !this.configured) {
    //    system = template.find('.system').value || null;
    //  }
    //  var record = null;
    //  var res = null
    //  var predicate = {'_id': this._id};
    //  // if the record is in HVAC, Lighting or Monitoring, update the record
    //  // but if it is in Unconfigured, remove it!
    //  var update = {'HVACZone': hvaczone,
    //                'LightingZone': lightingzone,
    //                'Room': room,
    //                'System': system,
    //                'configured': true};
    //  console.log("calling", this._id, update);
    //  Meteor.call('savemetadata', this._id, update, function() {
    //    console.log("returned!");
    //    path = path.replace(/\//g,'_');
    //    $('#notifications'+path).empty();
    //    $('#notifications'+path).append('<p id="success'+path+'" style="padding: 5px"><br/></p>');
    //    $('#success'+path).html('Successful!');
    //    $('#success'+path).css('background-color','#5cb85c');
    //    $('#success'+path).fadeOut(2000);
    //    if (system) {
    //      location.reload();
    //    }
    //  });
    //}
  });

  Template.configuration.isunconfigured = function() {
    return !this.configured
  };

  Template.configuration.rendered = function() {
      var myhvaczone = null;
      var mylightingzone = null;
      var myroom = null;
      var path = this.data.path;
      var predicate = {'_id': this.data._id};
      record = HVAC.findOne(predicate) || Lighting.findOne(predicate) || Monitoring.findOne(predicate);
      $('.autocompletefield').autocomplete(
            {
                source: function(request, response) {
                  var mykey = $(this).get(0).element.get(0).dataset['mykey'];
                  get_autocomplete_options(mykey, response);
                },
                minLength: 0,
            }
      );

      $('form').on('submit', function(e) {
        var inputs = $(this).find(':input');
        var towrite = {};
        _.each(inputs , function(val, idx) {
            towrite[val.dataset['mykey']] = val.value;
        });
        console.log("towrite");
        var update = {'HVACZone': towrite['HVACZone'],
                      'LightingZone': towrite['LightingZone'],
                      'Room': towrite['Room'],
                      'System': towrite['System'],
                      'configured': true};
        Meteor.call('savemetadata', towrite['_id'], towrite, function() {
          console.log("returned!");
        });
        console.log(towrite);
        e.preventDefault();
        return false;
      });
  };

  /*
   * This function extracts all the timeseries metadata from a record
   * and computes the intersection of keys to be displayed.
   *
   * This method should return a minimum subset of keys that are expected
   * by everyone:
   * - Building 
   * - Name
   * - Floor
   * - SourceName (static?)
   * - Driver (static)
   * - Site (static)
   * - System
   * - Role
   * - Device 
   * - Model (static)
   *
   * HVAC specific:
   * - HVACZone
   *
   * Lighting specific:
   * - Lightingzone
   *
   * Monitoring specific:
   * - HVACZone + Lightingzone
   *
   */
  Template.configuration.commonmetadata = function() {
      var tmp = find_by_id(this._id);
      var record = tmp[0];
      var type = tmp[1];
      var metadata = [];
      var path = fix_path(record.path);
      var common = common_metadata(record).Metadata;
      /*
       * Now, we add the system-specific stuff. Check if it is HVAC, Lighting or Monitoring
       */
      if (type == 'HVAC') {
        metadata.push({'path': path, 'key': 'HVACZone', 'val': common['HVACZone'] || '', 'static': false});
      }
      if (type == 'Lighting') {
        metadata.push({'path': path, 'key': 'LightingZone', 'val': common['LightingZone'] || '', 'static': false});
      }
      if (type == 'Monitoring') {
        metadata.push({'path': path, 'key': 'HVACZone', 'val': common['HVACZone'] || '', 'static': false});
        metadata.push({'path': path, 'key': 'LightingZone', 'val': common['LightingZone'] || '', 'static': false});
      }

      delete common['configured']; // unneeded
      delete common['LightingZone']; // delete this and the next one bc we used it earlier
      delete common['HVACZone'];


      common['Site'] = Meteor.settings.public.site;
      var required_keys = ['Room','Building','Name','Floor','System','Role','Device'];
      var static_keys = ['Site','Driver','Model','_id'];
      var static_vals = {}
      _.each(static_keys, function(key, idx) {
        static_vals[key] = common[key] || '';
        delete common[key];
      });
      static_vals['_id'] = this._id;
      // ensure all required keys are present
      _.each(required_keys, function(key, idx) {
        common[key] = common[key] || '';
      });
      // push all required key values onto the returned metadata list
      _.each(common, function(val, key) {
        metadata.push({'path': path,'key': key, 'val':val, 'static': false});
      });

      // add all static keys
      _.each(static_keys, function(key, idx) {
        metadata.push({'path': path, 'key': key, 'val': static_vals[key], 'static': true});
      });

      return metadata;
  };

  Template.configuration.derivedrooms = function() {
    var ret = [];
    if (Session.get('selectedhvaczone') != null) {
      ret = roomsForHVACZone(Session.get('selectedhvaczone'));
    } else {
      zone = hvaczoneByID(this._id);
      ret = roomsForHVACZone(zone);
      if (!zone) {
        zone = lightingzonebyId(this._id);
        ret = roomsForLightingZone(zone);
      }
    }
    return ret;
  };

  Template.contents.rendered = function() {
    $('#config_contents').empty();
    $('#config_contents').append("<ul></ul>");
    var items = [];
    _.each(this.data, function(val, idx) {
      items.push('<li>'+val+'</li>');
    });
    $('#config_contents').append(items.join(''));

  };


}
