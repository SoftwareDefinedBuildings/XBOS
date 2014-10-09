Meteor.startup(function() {
  console.log('startup');
  // populates the HVAC and Lighting collections
  Meteor.call('querysystem');
});

var metadatakeydescriptions = {
'LightingZone': 'Name for logical space that is under common lighting control, e.g. "Room 213 Overheads"',
'HVACZone': 'Name for the group of spaces that are controlled by the same thermostat, e.g. "South Offices"',
'Building': 'Name of the building',
'SourceName': 'Auto-generated name of sMAP Driver',
'System': 'Which domain this device belongs to (Auto-generated)',
'Driver': 'sMAP Driver module path',
'Device': 'What is this device? e.g. Thermostat, Lighting Controller, Sensor',
'Group': 'Unique number for a lighting controller (start at 1, 2, etc)',
'Floor': 'Which floor in the building this is installed',
'Model': 'The model of the device, e.g. "CT80 RTA"',
'Name': 'Human-readable name for your convenience',
'Room': 'Room where device is installed',
'Role': 'What purpose this device fulfills within the system, e.g. "Building Lighting", "Task Lighting", etc',
'Site': 'Auto-generated unique identifier for this installation',
'_id': 'Mongo record identifier',
};

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

Dashboard.day_names = {'7': 'sun', '1': 'mon', 
                       '2': 'tue', '3': 'wed', 
                       '4': 'thu', '5': 'fri', 
                       '6': 'sat'
};

UI.registerHelper('getSensorValue', function(obj) {
    var res = _.find(this.timeseries, function(val) {
        return val.Metadata.Sensor == obj;
    });
    var unit = res.Properties.UnitofMeasure;
    var p = Points.find({'uuid': res.uuid}).fetch()[0];
    var value = p.value;
    if (unit == 'C') {
      value = value * 1.8 + 32;
    }
    value = Number((value).toFixed(1));
    return value;
});


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

/*
 * Returns a text description of a metadata key
 */
UI.registerHelper('getDescription', function(key) {
    return metadatakeydescriptions[key] || '';
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
  var possible = Monitoring.find({'lightingzone': this[0].lightingzone}).fetch();
  return possible;
};

Template.hvac_zone_widget.sensors = function() {
  return Monitoring.find({'hvaczone': this.hvaczone});
};

Template.generalbuildingcolumn.powermeterAll = function() {
  // find everything with a /demand endpoint
  return Monitoring.find({'timeseries.demand': {'$exists': true}});
};

Template.generalbuildingcolumn.hasGeneralControl = function() {
   return (GeneralControl.find({}).fetch().length > 0);
}

Template.hvac_zone_widget.helpers({
  isOff: function(){
    var p = Points.findOne({'uuid': this.timeseries.hvac_state.uuid});
    return (p.value == 0);
  },
  isHeating: function(){
    var p = Points.findOne({'uuid': this.timeseries.hvac_state.uuid});
    return (p.value == 1);
  },
  isCooling: function(){
    var p = Points.findOne({'uuid': this.timeseries.hvac_state.uuid});
    return (p.value == 2);
  }
});

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

Template.room_detail.helpers({
  uuid: function(val) {
    if (this.timeseries[val]) {
      if (this.timeseries[val].Actuator) {
        return this.timeseries[val].Actuator.uuid+"_control";
      } else {
        return this.timeseries[val].uuid+"_control";
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
  } else if (this.data.Metadata.System == 'GeneralControl') {
    UI.insert(rend, $(pointid+'_control').get(0));
  }
};

Template.point_display.rendered = function(){
  var myuuid = this.data.uuid;
  var restrict = "uuid='" + this.data.uuid + "'";
  var q = "select data in (now -4h, now) where " + restrict;
  Meteor.call("query", q, function(err, res){
    if (res[0] != undefined){
      var mydata = jsonify(res[0].Readings);
      sparkline("#sparkline-" + myuuid, mydata, 300, 50, "last 4 hours");
    }
  });
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
    // get 4 hours of data 
    var qq = "select data in (now -4h, now) where " + restrict
    Meteor.call("query", qq, function(err, res){
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
                   .interpolate("step-before")
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

        temp = jsonify(temp.Readings);
        temp_cool = jsonify(temp_cool.Readings);
        temp_heat = jsonify(temp_heat.Readings);

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

        var focus = svg.append("g")
          .attr("class", "focus")
          .style("display", "none");

        focus.append("text")
          .attr("fill", "#696969")
          .attr("x", width - 5)
          .attr("y", height - 5)
          .attr("opacity", "0.8")
          .attr("font-size", "1.2em")
          .attr("text-anchor", "end")
          .text("last 4 hours")

        var myrect = focus.append("rect")
          .attr("x", 0)
          .attr("y", 0)
          .attr("width", 1)
          .attr("height", height)
          .attr("opacity", 0.5)

        var bisectTime = d3.bisector(function(d) { return d.time; }).left
        var formatValue = d3.format(".1f");

        focus.append("text")
          .attr("class", "hvac_tooltip")
          .attr("id", "temp_text") 
          .attr("dy", ".35em");

        focus.append("text")
          .attr("class", "hvac_tooltip")
          .attr("id", "temp_heat_text")
          .attr("fill", "red")
          .attr("dy", "1.75em");

        focus.append("text")
          .attr("class", "hvac_tooltip")
          .attr("id", "temp_cool_text")
          .attr("fill", "blue")
          .attr("dy", "-1.15em");

        svg.append("rect")
          .attr("class", "overlay")
          .attr("width", width)
          .attr("height", height)
          .on("mouseover", function() { focus.style("display", null); })
          .on("mouseout", function() { focus.style("display", "none"); })
          .on("mousemove", mousemove);

        function mousemove() {
          var xpos = d3.mouse(this)[0];
          var ypos = d3.mouse(this)[1];
          var x0 = x.invert(xpos)
          var ti = bisectTime(temp, x0, 1)
          var hi = bisectTime(temp_heat, x0, 1);
          var ci = bisectTime(temp_cool, x0, 1);

          if (temp[ti].value) { 
            var temp_tooltip = formatValue(temp[ti].value); 
            focus.select("#temp_text")
              .text(temp_tooltip)
          }
          if (temp_heat[hi].value) { 
            var temp_heat_tooltip = formatValue(temp_heat[hi].value); 
            focus.select("#temp_heat_text")
              .text(temp_heat_tooltip)
          }
          if (temp_cool[ci].value) { 
            var temp_cool_tooltip = formatValue(temp_cool[ci].value); 
            focus.select("#temp_cool_text")
              .text(temp_cool_tooltip)
          }

          var mytext = focus.selectAll(".hvac_tooltip");
          if ((width - xpos) < 40) {
            mytext.attr("text-anchor", "end").attr("dx", "-1em");
          } else {
            mytext.attr("text-anchor", "start").attr("dx", "1em");
          }
          myrect.attr("x", xpos);
          mytext.attr("x", xpos).attr("y", ypos);

        }

      }
      hvac_zone_summary("#HVAC-zone-summary-" + id, mydata);
    });
  });

  // render sparklines for sensors
  var sensors = Monitoring.find({'hvaczone': this.data.hvaczone}).fetch();
  _.each(sensors, function(s){
    var restrict = 'Path="' + s.path + '/temperature"';
    var q = "select data in (now -4h, now) where " + restrict;
    Meteor.call("query", q, function(err, res){
      if (res[0] != undefined){
        var mydata = jsonify(res[0].Readings);
        sparkline("#sparkline-temperature-container-" + s._id, mydata, 100, 30, "");
      }
    });
  });
  _.each(sensors, function(s){
    var restrict = 'Path="' + s.path + '/humidity"';
    var q = "select data in (now -4h, now) where " + restrict;
    Meteor.call("query", q, function(err, res){
      var mydata = jsonify(res[0].Readings);
      sparkline("#sparkline-humidity-container-" + s._id, mydata, 100, 30, "");
    });
  });

}

Template.power_meter_widget.rendered = function(){
  var restrict = 'Path="' + this.data.path + '/demand"';
  var myid = this.data._id;
  var q = "select data in (now -4h, now) where " + restrict;
  Meteor.call("query", q, function(err, res){
    if (err) {
        console.log(err);
    }
    var mydata = res[0].Readings;
    mydata = jsonify(mydata);
    sparkline("#sparkline-container-" + myid, mydata, 250, 50, "last 4 hours");
  });
}
