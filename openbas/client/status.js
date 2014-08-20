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
  
  get_source_path = function(path) {
    return path.slice(0,path.lastIndexOf('/'));
  }

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

    'click .save': function(e, template) {
      var path = this.path;
      var hvaczone = template.find('.hvaczones').value || null;
      var lightingzone = template.find('.lightingzones').value || null;
      var room = template.find('.rooms').value || null;
      var system = null;
      if (this.configured == null || !this.configured) {
        system = template.find('.system').value || null;
      }
      var record = null;
      var res = null
      var predicate = {'_id': this._id};
      // if the record is in HVAC, Lighting or Monitoring, update the record
      // but if it is in Unconfigured, remove it!
      var update = {'HVACZone': hvaczone,
                    'LightingZone': lightingzone,
                    'Room': room,
                    'System': system,
                    'configured': true};
      console.log("calling", this._id, update);
      Meteor.call('savemetadata', this._id, update);//, function() {
//        console.log("returned!", res);
//        path = path.replace(/\//g,'_');
//        $('#notifications'+path).empty();
//        $('#notifications'+path).append('<p id="success'+path+'" style="padding: 5px"><br/></p>');
//        $('#success'+path).html('Successful!');
//        $('#success'+path).css('background-color','#5cb85c');
//        $('#success'+path).fadeOut(2000);
//      });
      //record['configured'] = true;
      ////TODO: save this metadata update to the archiver
      //if (res == 1) {
      //  // successful
      //  var path = this.path.replace(/\//g,'_');
      //  $('#notifications'+path).empty();
      //  $('#notifications'+path).append('<p id="success'+path+'" style="padding: 5px"><br/></p>');
      //  $('#success'+path).html('Successful!');
      //  $('#success'+path).css('background-color','#5cb85c');
      //  $('#success'+path).fadeOut(2000);
      //  //res = Unconfigured.remove({'_id': this._id});
      //}

    }
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
      if (record) {
        myhvaczone = record.hvaczone;
        mylightingzone = record.lightingzone;
        myroom = record.room;
      }
      $('.lightingzones').find('option').removeClass('selected')
      _.each($('.lightingzones').find('option'), function(val, idx) {
        if (val.value == mylightingzone) {
            mypath = path.replace(/\//g,'_');
            $('#device_'+mypath+' .lightingzones').val(val.value);
        }
      });
      $('.hvaczones').find('option').removeClass('selected')
      _.each($('.hvaczones').find('option'), function(val, idx) {
        if (val.value == myhvaczone) {
            mypath = path.replace(/\//g,'_');
            $('#device_'+mypath+' .hvaczones').val(val.value);
        }
      });
      $('.rooms').find('option').removeClass('selected')
      _.each($('.rooms').find('option'), function(val, idx) {
        if (val.value == myroom) {
            mypath = path.replace(/\//g,'_');
            $('#device_'+mypath+' .room').val(val.value);
        }
      });
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
