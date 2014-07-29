if (Meteor.isClient) {
//  Template.lighting.rendered = function() {
//    var query = "select * where Metadata/Site = '" + Meteor.settings.public.site + "'";
//    query += " and Metadata/Type = 'Light Group';";
//    Meteor.call('query', query, function(err, res) {
//      if (err) {
//        console.log(err);
//        return
//      }
//      if (!res[0]) {
//        console.log("No results found for",query);
//        return
//      }
//      console.log(query, res);
//      var renderedlight = UI.render(Template.buildinglighting);
//      UI.insert(renderedlight, $('#buildinglighting'));
//    });
//
//  };

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
      var groups = $.unique(_.map(res, function(o) { return o.Metadata.Name}));
      var l = {'lightgroups': groups};
      var rendered = UI.renderWithData(Template.lightgrouprender, l);
      UI.insert(rendered, $('#buildinglighting').get(0));
      $.each(groups, function(idx, val) {
        // for each group, 
      });
    });
  };

  Template.lightgroup.value = function() {
    return this;
  };

  Template.lighting.helpers({
    has_bri: function(template) {
      console.log("check bri", this);
      return true
    },
    has_hue: function(template) {
      console.log("check bri", this);
      return true
    },
    has_on: function(template) {
      console.log("check bri", this);
      return true
    }
  });
}
