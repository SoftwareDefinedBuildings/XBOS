Meteor.startup(function() {
    console.log('startup');
    // populates the HVAC and Lighting collections
    Meteor.call('querysystem');
});


if (Meteor.isClient) {

  var Dashboard = {};

  Dashboard.jsonify = function (readings){
    return _.map(readings, function(r){
      var o = {};
      o.time = r[0];
      o.value = r[1];
      return o;
    });
  } 

  Dashboard.sparkline = function(elemId, data, width, height, display_range) {
    var x = d3.scale.linear().range([0, width]);
    var y = d3.scale.linear().range([height, 0]);
    var line = d3.svg.line()
                 .interpolate("basis")
                 .x(function(d) { return x(d.time); })
                 .y(function(d) { return y(d.value); });
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

    if (display_range){
      var extents_label = "[<span class='sparkline-min'>" + yextents[0].toFixed(2) + "</span>,";
      extents_label += "<span class='sparkline-max'>" + yextents[1].toFixed(2) + "</span>]";
      d3.select('#sparkline-extents-' + id)
        .html(extents_label)
    }
  }

  UI.registerHelper('getValue', function(obj) {
    var unit = this.timeseries[obj].Properties.UnitofMeasure;
    var p = Points.find({'uuid': this.timeseries[obj].uuid}).fetch()[0];
    var value = p.value;
    if (unit == 'C') {
      value = value * 1.8 + 32;
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

  Template.hvac_zone_widget.rendered = function(){

    var restrict0 = 'Path="' + this.data.path;
    var restrict = restrict0 + '/temp_cool" or '
                 + restrict0 + '/temp_heat" or '
                 + restrict0 + '/temp"';
    var id = this.data._id;
    var q = "select * where " + restrict;
    Meteor.call("query", q, function(err, res) {
      var tags = res;
      Meteor.call("latest", restrict, 100, function(err, res){
        var mydata = _.map(res, function(o){
          var tag = _.find(tags, function(t){ return t.uuid == o.uuid });
          var rv = _.extend(o, tag);
          return rv
        });
        var width = 300;
        var height = 100;
        var x = d3.scale.linear().range([0, width]);
        var y = d3.scale.linear().range([height, 0]);
        var line = d3.svg.line()
                     .x(function(d) { return x(d.time); })
                     .y(function(d) { return y(d.value); });

        function hvac_zone_summary(elemId, data){
          var extents = _.map(data, function(d){
            var readings = _.zip.apply(_, d.Readings);
            var timestamps = readings[0];
            var values = readings[1];
            rv = {
              'xmin': _.min(timestamps),
              'ymin': _.min(values),
              'xmax': _.max(timestamps),
              'ymax': _.max(values),
            }
            return rv
          });
          var yextent = [ _.min(_.pluck(extents, 'ymin')), _.max(_.pluck(extents, 'ymax'))];
          var xextent = [ _.min(_.pluck(extents, 'xmin')), _.max(_.pluck(extents, 'xmax'))];
          x.domain(xextent);
          y.domain(yextent);

          var temp = _.find(data, function(d){
            return _.last(d.Path.split("/")) == "temp";
          });
          var temp_cool = _.find(data, function(d){
            return _.last(d.Path.split("/")) == "temp_cool";
          });
          var temp_heat = _.find(data, function(d){
            return _.last(d.Path.split("/")) == "temp_heat";
          });

          function d3ify(d){
            var r = {};
            r.time = d[0];
            r.value = d[1];
            return r;
          }

          temp = _.map(temp.Readings, d3ify);
          temp_cool = _.map(temp_cool.Readings, d3ify);
          temp_heat = _.map(temp_heat.Readings, d3ify);

          var svg = d3.select(elemId)
            .append('svg')
            .attr('class', 'HVAC-zone-summary')
            .attr('width', width)
            .attr('height', height)

          svg.append('path')
            .datum(temp)
            .attr('class', 'templine')
            .attr('d', line);

          svg.append('path')
            .datum(temp_cool)
            .attr('class', 'cooltempline')
            .attr('d', line);

          svg.append('path')
            .datum(temp_heat)
            .attr('class', 'heattempline')
            .attr('d', line);

        }
        hvac_zone_summary("#HVAC-zone-summary-" + id, mydata);
      });
    });

    // render sparklines for sensors
    var sensors = Monitoring.find({'hvaczone': this.data.zone}).fetch();
    console.log(sensors);
    _.each(sensors, function(s){
      var restrict = 'Path="' + s.path + '/temperature"';
      Meteor.call("latest", restrict, 100, function(err, res){
        var mydata = Dashboard.jsonify(res[0].Readings);
        Dashboard.sparkline("#sparkline-temperature-container-" + s._id, mydata, 100, 25, false);
      });
    });
    _.each(sensors, function(s){
      var restrict = 'Path="' + s.path + '/humidity"';
      Meteor.call("latest", restrict, 100, function(err, res){
        var mydata = Dashboard.jsonify(res[0].Readings);
        Dashboard.sparkline("#sparkline-humidity-container-" + s._id, mydata, 100, 25, false);
      });
    });

  }

  Template.power_meter_widget.rendered = function(){
    var restrict = 'Path="' + this.data.path + '/demand"';
    var id = this.data._id;
    Meteor.call("latest", restrict, 1000, function(err, res){
      var mydata = res[0].Readings;
      mydata = Dashboard.jsonify(mydata);
      Dashboard.sparkline("#sparkline-container-" + id, mydata, 250, 50, true);
    });
  }

}
