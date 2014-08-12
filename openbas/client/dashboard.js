Meteor.startup(function() {
    console.log('startup');
    // populates the HVAC and Lighting collections
    Meteor.call('querysystem');
});


if (Meteor.isClient) {

  UI.registerHelper('getValue', function(obj) {
    var unit = this.timeseries[obj].Properties.UnitofMeasure;
    var p = Points.find({'uuid': this.timeseries[obj].uuid}).fetch()[0];
    var value = p.value;
    if (unit == 'C') {
      value = value * .8 + 32;
    }
    return Number((value).toFixed(1));
  });

  Template.dashboard.created = function() {
    // populates the HVAC and Lighting collections
    Meteor.call('querysystem');
  };

  Template.hvacbuildingcolumn.HVACAll = function() {
    return HVAC.find({});
  };
  
  Template.lightingbuildingcolumn.LightingAll = function() {
    var lighting = Lighting.find({'role': 'Building Lighting'}).fetch();
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
    return this;
  };

  Template.light_zone_widget.internals = function() {
    var lighting = Lighting.find({'role': 'Task Lighting', 'zone': this[0].zone});
    return lighting;
  };

  Template.light_zone_widget.sensors = function() {
    return Monitoring.find({'lightingzone': this[0].zone});
  };

  Template.hvac_zone_widget.sensors = function() {
    return Monitoring.find({'hvaczone': this.zone});
  };

  Template.generalbuildingcolumn.powermeterAll = function() {
    // find everything with a /demand endpoint
    return Monitoring.find({'timeseries.demand': {'$exists': true}});
  };

  Template.generalbuildingcolumn.globalschedule = function() {
    var sched = {};
    sched['weekday'] = [];
    sched['weekend'] = [];
    sched['weekday'][0] = {'name': 'Morning', 'time': '0730', 'heatsp': 72, 'coolsp': 83};
    sched['weekday'][1] = {'name': 'Afternoon', 'time': '1330', 'heatsp': 70, 'coolsp': 80};
    sched['weekday'][2] = {'name': 'Evening', 'time': '1830', 'heatsp': 50, 'coolsp': 90};

    sched['weekend'][0] = {'name': 'Morning','time': '0930', 'heatsp': 65, 'coolsp': 85};
    sched['weekend'][1] = {'name': 'Afternoon','time': '1730', 'heatsp': 70, 'coolsp': 80};
    sched['weekend'][2] = {'name': 'Evening','time': '2100', 'heatsp': 50, 'coolsp': 90};

    return sched;
  };

  Template.generalbuildingcolumn.rendered = function() {
    var m = moment();
    $('.day').removeClass('info');
    $('#day'+m.day()).addClass('info');

    _.each($('.schedulerow'), function(val, idx) {
      var t = moment(val.getAttribute('data-time'), 'HHmm');
      var name = val.getAttribute('id');
      if (m.unix() > t.unix()) {
        $('.schedulerow').removeClass('info');
        $('#'+name).addClass('info');
      }
    });

    console.log($('.schedulerow'));
  };

  Template.generalbuildingcolumn.daytype = function() {
    var m = moment();
    if (m.day() < 6) {
      return 'Weekday';
    } else {
      return 'Weekend';
    }
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

  Template.power_meter_widget.rendered = function(){
    console.log(this.data);
    var restrict = 'Path="' + this.data.path + '/demand"';
    var id = this.data._id;
    Meteor.call("latest", restrict, 100, function(err, res){
      var width = 100;
      var height = 25;
      var x = d3.scale.linear().range([0, width]);
      var y = d3.scale.linear().range([height, 0]);
      var line = d3.svg.line()
                   .x(function(d) { return x(d.time); })
                   .y(function(d) { return y(d.value); });

      function sparkline(elemId, data) {
        x.domain(d3.extent(data, function(d) { return d.time; }));
        var yextents = d3.extent(data, function(d) { return d.value; });
        y.domain(yextents);

        d3.select(elemId)
          .append('svg')
          .attr('width', width)
          .attr('height', height)
          .append('path')
          .datum(data)
          .attr('class', 'sparkline')
          .attr('d', line);

        var extents_label = "[<span class='sparkline-min'>" + yextents[0].toFixed(2) + "</span>,";
        extents_label += "<span class='sparkline-max'>" + yextents[1].toFixed(2) + "</span>]";
        d3.select('#sparkline-extents-' + id)
          .html(extents_label)

      }

      var mydata = res[0].Readings;
      mydata = _.map(mydata, function(d){
        var r = {};
        r.time = d[0];
        r.value = d[1];
        return r;
      });
      sparkline("#sparkline-container-" + id, mydata);
    });
  }

}
