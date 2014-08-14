if (Meteor.isClient) {

  Session.set('selectedhvaczone', null);

  hvaczones = function() {
    return _.uniq( _.filter( _.pluck(Rooms.find().fetch(), 'HVACZone'), function(o) { return o != null; }));
  };

  roomsForHVACZone = function(zone) {
    if (!zone) {
      return []
    }
    return _.pluck(Rooms.find({'HVACZone':zone}).fetch(), 'RoomNumber');
  };

  UI.registerHelper('fixPath', function(p) {
    return p.replace(/\//g,'_');
  });

  UI.registerHelper('hvaczones', function() {
    return hvaczones();
  });

  Template.status.sources = function () {
    /*
     * Grabs all the HVAC, Lighting and Monitoring points. These
     * have been configured, so we can read their metadata. Thanks
     * to the 'querysystem' function, thse are pre-aggregated by
     * their driver path instead of the individual timeseries
     */
    var sources = [];
    sources.push.apply(sources, HVAC.find().fetch());
    sources.push.apply(sources, Lighting.find().fetch());
    sources.push.apply(sources, Monitoring.find().fetch());
    return sources
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
    'click div': function(e) {
        var path = this.path;
        var fixedpath = this.path.replace(/\//g,'_');
    },

    'change .hvaczones': function(e, template) {
        Session.set('selectedhvaczone', template.find('.hvaczones').value);
    }
  });

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
