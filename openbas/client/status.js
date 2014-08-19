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
      record = HVAC.findOne({'_id': _id})
      if (record) {
        return record.zone;
      }
      record = Lighting.findOne({'_id': _id})
      if (record) {
        return record.hvaczone;
      }
      record = Monitoring.findOne({'_id': _id})
      if (record) {
        return record.hvaczone;
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
   * Searches the 3 collections HVAC, Lighting and Metadata
   * for an aggregate path that's the same as our new point.
   * If we find one, it means we've been placed into an additonal
   * collection and are probably configured. If not, then we are unconfigured,
   * so we add ourselves to the Unconfigured collection
   */
  Template.status.rendered = function() {
    Points.find().observe({
    added: function(doc) {
        var found = false;
        _.each([HVAC, Lighting, Monitoring], function(system, index) {
            if (found) { return }
            var allpaths = _.pluck(system.find().fetch(), 'path')
            if (_.contains(allpaths, get_source_path(doc.Path))) {
                found = true;
                return
            }
        });
        if (!found) {
          console.log("Found new unconfigured point",doc);
          if (!Unconfigured.findOne({'uuid': doc.uuid})) {
            Unconfigured.insert(doc);
          }
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
      var hvaczone = template.find('.hvaczones').value;
      var lightingzone = template.find('.lightingzones').value;
      var room = template.find('.rooms').value;
      var record = null;
      var res = null
      record = HVAC.findOne({'_id': this._id})
      if (record) {
        res = HVAC.update(this._id, {$set: {'zone': hvaczone, 'lightingzone': lightingzone, 'room': room}});
      }
      record = Lighting.findOne({'_id': this._id})
      if (record) {
        res = Lighting.update(this._id, {$set: {'zone': lightingzone, 'hvaczone': hvaczone, 'room': room}});
      }
      record = Monitoring.findOne({'_id': this._id})
      if (record) {
        res = Monitoring.update(this._id, {$set: {'lightingzone': lightingzone, 'hvaczone': hvaczone, 'room': room}});
      }
      if (res == 1) {
        // successful
        console.log(this);
        var path = this.path.replace(/\//g,'_');
        $('#notifications'+path).empty();
        $('#notifications'+path).append('<p id="success'+path+'" style="padding: 5px"><br/></p>');
        $('#success'+path).html('Successful!');
        $('#success'+path).css('background-color','#5cb85c');
        $('#success'+path).fadeOut(2000);
      }

    }
  });

  Template.configuration.rendered = function() {
      var myhvaczone = null;
      var mylightingzone = null;
      var myroom = null;
      var path = this.data.path;
      record = HVAC.findOne({'_id': this.data._id})
      if (record) {
        myhvaczone = record.zone;
        mylightingzone = record.lightingzone;
        myroom = record.room;
      }
      record = Lighting.findOne({'_id': this.data._id})
      if (record) {
        myhvaczone = record.hvaczone;
        mylightingzone = record.zone;
        myroom = record.room;
      }
      record = Monitoring.findOne({'_id': this.data._id})
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
      console.log(this, zone);
      ret = roomsForHVACZone(zone);
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
