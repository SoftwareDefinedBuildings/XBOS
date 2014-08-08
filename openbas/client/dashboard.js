Meteor.startup(function() {
    console.log('startup');
    // populates the HVAC and Lighting collections
    Meteor.call('querysystem');
});


if (Meteor.isClient) {

  UI.registerHelper('getValue', function(obj) {
    var p = Points.find({'uuid': this.timeseries[obj].uuid}).fetch()[0];
    return p.value;
  });

  Template.dashboard.created = function() {
    // populates the HVAC and Lighting collections
    Meteor.call('querysystem');
  };

  Template.hvacbuildingcolumn.HVACAll = function() {
    return HVAC.find({});
  };
  
  Template.lightingbuildingcolumn.LightingAll = function() {
    var lighting = Lighting.find({}).fetch();
    // for each unique zone
    var zones = [];
    _.each(_.uniq(_.pluck(lighting, 'zone')), function(val, idx) {
      var groups = _.filter(lighting, function(o) { return o.zone == val; });
      zones[idx] = groups;
    });
    return zones;
  };

  Template.light_zone_widget.zone = function() {
    return this[0].zone;
  };

  Template.light_zone_widget.groups = function() {
    console.log(this);
    return this;
  };
  Template.light_zone_widget.sensors = function() {
    return Monitoring.find({'lightingzone': this.zone});
  };

  Template.hvac_zone_widget.sensors = function() {
    return Monitoring.find({'hvaczone': this.zone});
  };

  Template.generalbuildingcolumn.powermeterAll = function() {
    // find everything with a /demand endpoint
    return Monitoring.find({'timeseries.demand': {'$exists': true}});
  };

  Template.zone_detail.points = function() {
    return this.points;
  };

  Template.zone_detail.helpers({
    is_hvac: function(val) {
      return val == 'hvac';
    },
    is_lighting: function(val) {
      return val == 'lighting';
    }
  });

  Template.thermostat.helpers({
    has: function(val) {
      return this.timeseries[val]
    },
    uuid: function(val) {
      if (this.timeseries[val]) {
        if (this.timeseries[val].Actuator) {
          return this.timeseries[val].Actuator.uuid+"_hvac";
        } else {
          return this.timeseries[val].uuid+"_hvac";
        }
      }
      return ''
    }
  });

  Template.lightinggroup.helpers({
    has: function(val) {
      return this.timeseries[val]
    },
    uuid: function(val) {
      if (this.timeseries[val]) {
        if (this.timeseries[val].Actuator) {
          return this.timeseries[val].Actuator.uuid+"_lighting";
        } else {
          return this.timeseries[val].uuid+"_lighting";
        }
      }
      return ''
    }
  });

  Template.point.rendered = function(arg) {
    var p = Points.find({'uuid': this.data.uuid}).fetch()[0];
    if (p.ActuatorUUID) {
      var rend = UI.renderWithData(Template.actuator_display, p);
      var pointid = '#'+p.ActuatorUUID;
    } else {
      var rend = UI.renderWithData(Template.point_display, p);
      var pointid = '#'+p.uuid;
    }
    if (this.data.Metadata.System == 'Lighting') {
      UI.insert(rend, $(pointid+'_lighting').get(0));
    } else if (this.data.Metadata.System == 'HVAC') {
      UI.insert(rend, $(pointid+'_hvac').get(0));
    }
  };

}
