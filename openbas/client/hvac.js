if (Meteor.isClient) {
  Template.hvac.rendered = function() {
    var query = "select * where Metadata/Site = '" + Meteor.settings.public.site + "'";
    query += " and Metadata/Type = 'HVAC Group';";

    Meteor.call('query', query, function(err, res) {
      if (err) {
        console.log(err);
        return
      }
      if (!res[0]) {
        console.log("No results found for",query);
        return
      }
      // get unique list of Name
      var groups = $.unique(_.map(res, function(o) { return o.Metadata.Name}));
      var l = {'hvacgroups': groups};
      var rendered = UI.renderWithData(Template.hvacgrouprender, l);
      UI.insert(rendered, $('#buildinghvac').get(0));
      // loop through group Names, and group points
      $.each(groups, function(idx, val) {
        // get all timeseries for this group
        var ts_list = _.filter(res, function(o) {
                return o.Metadata.Name == val;
        });

        // create group obj
        var group = {'Timeseries': ts_list};
        var helpers = {};

        _.each(["temp", "humidity", "hvac_state", "temp_heat", "temp_cool",
            "hold", "override", "hvac_mode","fan_mode" ], function(val, idx) {
              var re = new RegExp(val+'$');
              var t = _.filter(ts_list, function(o) {
                return o.Path.match(re);
              });
              if (t) {
                group[val] = t[0];
              }
          });

        var rendered_hvac = UI.renderWithData(Template.hvacobj, group);
        UI.insert(rendered_hvac, $('#'+val.replace(/ /g,'_')).get(0));

      });
    });

  };

  Template.hvacobj.helpers({
    has: function(val) {
      console.log("has", val, this);
      return this[val]
    },
    uuid: function(val) {
      if (this[val]) {
        return this[val].Actuator.uuid+"_hvac";
      }
      return ''
    }
  });

  Template.hvacgroup.value = function() {
    return this;
  };

  Template.hvacgroup.id_value = function() {
    return this.replace(/ /g, '_');
  };

  //Template.hvacobj.helpers({
  //  has_bri: function(template) {
  //    return this.bri;
  //  },
  //  has_hue: function(template) {
  //    return this.hue;
  //  },
  //  has_on: function(template) {
  //    return this.on;
  //  },
  //  bri_uuid: function(template) {
  //    return this.bri.Actuator.uuid+"_hvac";
  //  },
  //  hue_uuid: function(template) {
  //    return this.hue.Actuator.uuid+"_hvac";
  //  },
  //  on_uuid: function(template) {
  //    return this.on.Actuator.uuid+"_hvac";
  //  },
  //});

  //Template.bri.rendered = function() {
  //  var p = Points.find({'uuid': this.data.bri.uuid}).fetch()[0];
  //  var rend = UI.renderWithData(Template.actuator_display, p);
  //  UI.insert(rend, $('#'+p.ActuatorUUID+"_hvac").get(0));
  //};

  //Template.hue.rendered = function() {
  //  var p = Points.find({'uuid': this.data.hue.uuid}).fetch()[0];
  //  var rend = UI.renderWithData(Template.actuator_display, p);
  //  UI.insert(rend, $('#'+p.ActuatorUUID+"_hvac").get(0));
  //};

  //Template.on.rendered = function() {
  //  var p = Points.find({'uuid': this.data.on.uuid}).fetch()[0];
  //  var rend = UI.renderWithData(Template.actuator_display, p);
  //  UI.insert(rend, $('#'+p.ActuatorUUID+"_hvac").get(0));
  //};
}
