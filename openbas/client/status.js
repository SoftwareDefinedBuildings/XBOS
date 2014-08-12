if (Meteor.isClient) {

  Template.status.sources = function () {
    var sources = [];
    sources.push.apply(sources, HVAC.find().fetch());
    sources.push.apply(sources, Lighting.find().fetch());
    sources.push.apply(sources, Monitoring.find().fetch());
    return sources
  };
}
