Meteor.startup(function() {
  console.log('startup');
  // populates the HVAC and Lighting collections
  Meteor.call('querysystem');
});

var Dashboard = {};

Dashboard.render_schedules = function(){
  // This seems to insure that schedules and master_schedule are loaded
  // .. but I thought this would be taken care of by waitOn?
  Meteor.subscribe('schedules', function(){
    Meteor.subscribe('master_schedule', function(){
      var scheds = Schedules.find().fetch();
      Dashboard.master_schedule = MasterSchedule.findOne({});

      // Shouldn't be neeed when we remove autopublish
      delete Dashboard.master_schedule._id;

      _.each(Dashboard.master_schedule, function(val, key){
        var day_sched = _.find(scheds, function(s){ return s.name == val });
        $('#'+key).css('background-color', day_sched.color);
      });

      /*
      $(".day-tooltip").tooltip({
        title: function(){
          return Dashboard.master_schedule[this.id];
        },
        placement: 'bottom',
      });
      */

      var m = moment();
      $('.day').removeClass('current-day');
      $('#'+Dashboard.day_names[m.day()]).addClass('current-day');

      _.each($('.schedulerow'), function(val, idx) {
        var t = moment(val.getAttribute('data-time'), 'HH:mm');
        var name = val.getAttribute('id');
        if (m.unix() > t.unix()) {
          $('.schedulerow').removeClass('current-period');
          $('#'+name).addClass('current-period');
        }
      });
    });
  });
};

Dashboard.jsonify = function (readings){
  return _.map(readings, function(r){
    var o = {};
    o.time = r[0];
    o.value = r[1];
    return o;
  });
};

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
    d3.select(elemId)
      .html(extents_label)
  }
};

Dashboard.day_names = {'7': 'sun', '1': 'mon', 
                       '2': 'tue', '3': 'wed', 
                       '4': 'thu', '5': 'fri', 
                       '6': 'sat'
};

UI.registerHelper('getValue', function(obj) {
  if (this.timeseries[obj] != undefined){
    var unit = this.timeseries[obj].Properties.UnitofMeasure;
    var p = Points.find({'uuid': this.timeseries[obj].uuid}).fetch()[0];
    var value = p.value;
    if (unit == 'C') {
      value = value * 1.8 + 32;
    }
    return Number((value).toFixed(1));
  } 
});

Template.dashboard.created = function() {
  // populates the HVAC and Lighting collections
  Meteor.call('querysystem');
};

Template.general_control_widget.GeneralControlAll = function() {
  return GeneralControl.find({});
};

Template.hvacbuildingcolumn.HVACAll = function() {
  return HVAC.find({});
};

Template.lightingbuildingcolumn.LightingAll = function() {
  var lighting = Lighting.find({'role': 'Building Lighting'}).fetch();
  // for each unique zone
  var zones = [];
  _.each(_.uniq(_.pluck(lighting, 'lightingzone')), function(val, idx) {
    var groups = _.filter(lighting, function(o) { return o.lightingzone == val; });
    zones[idx] = groups;
  });
  return zones;
};

Template.light_zone_widget.zone = function() {
  return this[0].lightingzone;
};

Template.light_zone_widget.groups = function() {
  return this;
};

Template.light_zone_widget.internals = function() {
  var lighting = Lighting.find({'role': 'Task Lighting', 'lightingzone': this[0].lightingzone});
  return lighting;
};

Template.light_zone_widget.sensors = function() {
  return Monitoring.find({'lightingzone': this[0].lightingzone});
};

Template.hvac_zone_widget.sensors = function() {
  return Monitoring.find({'hvaczone': this.hvaczone});
};

Template.generalbuildingcolumn.powermeterAll = function() {
  // find everything with a /demand endpoint
  return Monitoring.find({'timeseries.demand': {'$exists': true}});
};

Template.schedule_widget.helpers({
  isNamed: function(path){
    return path == this.path;
  }
});

Template.schedule_widget.schedule = function(){
  var m = moment();
  var master = MasterSchedule.findOne({});
  var sch_name = master[Dashboard.day_names[m.day()]]
  var sched = Schedules.find({'name': sch_name}).fetch()[0];
  return sched;
}; 

Template.schedule_widget.rendered = Dashboard.render_schedules;

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
    Meteor.call("latest", restrict, 1000, function(err, res){
      var mydata = _.map(res, function(o){
        var tag = _.find(tags, function(t){ return t.uuid == o.uuid });
        var rv = _.extend(o, tag);
        return rv
      });
      var margin = 30;
      var width = $(window).width() / 3 - 2 * margin; 
      var height = 100;
      var x = d3.scale.linear().range([0, width]);
      var y = d3.scale.linear().range([height, 0]);
      var line = d3.svg.line()
                   .interpolate("basis")
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
          return rv;
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

        temp = Dashboard.jsonify(temp.Readings);
        temp_cool = Dashboard.jsonify(temp_cool.Readings);
        temp_heat = Dashboard.jsonify(temp_heat.Readings);

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
  var sensors = Monitoring.find({'hvaczone': this.data.hvaczone}).fetch();
  _.each(sensors, function(s){
    var restrict = 'Path="' + s.path + '/temperature"';
    Meteor.call("latest", restrict, 100, function(err, res){
      if (res[0] != undefined){
        console.log(res[0]);
        var mydata = Dashboard.jsonify(res[0].Readings);
        Dashboard.sparkline("#sparkline-temperature-container-" + s._id, mydata, 100, 25, false);
      }
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
  var myid = this.data._id;
  Meteor.call("latest", restrict, 1000, function(err, res){
    if (err) {
        console.log(err);
    }
    var mydata = res[0].Readings;
    mydata = Dashboard.jsonify(mydata);
    Dashboard.sparkline("#sparkline-container-" + myid, mydata, 250, 50, true);
  });
}
