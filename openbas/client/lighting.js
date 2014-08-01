if (Meteor.isClient) {
  Template.lighting.rendered = function() {
    var query = "select * where Metadata/Site = '" + Meteor.settings.public.site + "'";
    query += " and Metadata/Type = 'Light Group';";

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
      var l = {'lightgroups': groups};
      var rendered = UI.renderWithData(Template.lightgrouprender, l);
      UI.insert(rendered, $('#buildinglighting').get(0));
      // loop through group Names, and group points
      $.each(groups, function(idx, val) {
        // get all timeseries for this group
        var ts_list = _.filter(res, function(o) {
                return o.Metadata.Name == val;
        });

        // create group obj
        var group = {'Timeseries': ts_list};

        // populates the bri object
        var bri = _.filter(ts_list, function(o) {
          return o.Path.match(/bri$/);
        });
        if (bri) {
          group.bri = bri[0];
        }

        var hue = _.filter(ts_list, function(o) {
          return o.Path.match(/hue$/);
        });
        if (hue) {
          group.hue = hue[0];
        }

        var on = _.filter(ts_list, function(o) {
          return o.Path.match(/on$/);
        });
        if (on) {
          group.on = on[0];
        }

        var rendered_light = UI.renderWithData(Template.lightobj, group);
        UI.insert(rendered_light, $('#'+val.replace(/ /g,'_')).get(0));
      });
    });
  };

  Template.lightgroup.value = function() {
    return this;
  };

  Template.lightgroup.id_value = function() {
    return this.replace(/ /g, '_');
  };

  Template.lightobj.helpers({
    has_bri: function(template) {
      return this.bri;
    },
    has_hue: function(template) {
      return this.hue;
    },
    has_on: function(template) {
      return this.on;
    },
    bri_uuid: function(template) {
      return this.bri.Actuator.uuid+"_light";
    },
    hue_uuid: function(template) {
      return this.hue.Actuator.uuid+"_light";
    },
    on_uuid: function(template) {
      return this.on.Actuator.uuid+"_light";
    },
  });

  Template.bri.rendered = function() {
    var p = Points.find({'uuid': this.data.bri.uuid}).fetch()[0];
    var rend = UI.renderWithData(Template.actuator_display, p);
    UI.insert(rend, $('#'+p.ActuatorUUID+"_light").get(0));
  };

  Template.hue.rendered = function() {
    var p = Points.find({'uuid': this.data.hue.uuid}).fetch()[0];
    var rend = UI.renderWithData(Template.actuator_display, p);
    UI.insert(rend, $('#'+p.ActuatorUUID+"_light").get(0));
  };

  Template.on.rendered = function() {
    var p = Points.find({'uuid': this.data.on.uuid}).fetch()[0];
    var rend = UI.renderWithData(Template.actuator_display, p);
    UI.insert(rend, $('#'+p.ActuatorUUID+"_light").get(0));
  };
}
