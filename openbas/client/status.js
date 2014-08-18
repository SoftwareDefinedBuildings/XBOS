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


  UI.registerHelper('fixPath', function(p) {
    return p.replace(/\//g,'_');
  });

  UI.registerHelper('hvaczones', function() {
    return hvaczones();
  });

  UI.registerHelper('lightingzones', function() {
    return lightingzones();
  });

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
      record = HVAC.findOne({'_id': this._id})
      if (record) {
        HVAC.update(this._id, {$set: {'zone': hvaczone, 'room': room}});
      }
      record = Lighting.findOne({'_id': this._id})
      if (record) {
        Lighting.update(this._id, {$set: {'zone': lightingzone, 'room': room}});
      }
      record = Monitoring.findOne({'_id': this._id})
      if (record) {
        Monitoring.update(this._id, {$set: {'lightingzone': lightingzone, 'hvaczone': hvaczone, 'room': room}});
      }
      //TODO: give notification of successful save

    }
  });

  Template.configuration.rendered = function() {
      console.log("rendered",this);
      var myhvaczone = null;
      var mylightingzone = null;
      var path = this.data.path;
      record = HVAC.findOne({'_id': this.data._id})
      if (record) {
        myhvaczone = record.zone;
        mylightingzone = '';
      }
      record = Lighting.findOne({'_id': this.data._id})
      if (record) {
        myhvaczone = ''
        mylightingzone = record.zone;
      }
      record = Monitoring.findOne({'_id': this.data._id})
      if (record) {
        myhvaczone = record.hvaczone;
        mylightingzone = record.lightingzone;
      }
      console.log(myhvaczone, mylightingzone);
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
  };

  Template.configuration.derivedrooms = function() {
    var ret = [];
    if (Session.get('selectedhvaczone') != null) {
      ret = roomsForHVACZone(Session.get('selectedhvaczone'));
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
