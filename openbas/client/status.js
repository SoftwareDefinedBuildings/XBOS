if (Meteor.isClient) {

  Template.status.sources = function () {
    var sources = [];
    sources.push.apply(sources, HVAC.find().fetch());
    sources.push.apply(sources, Lighting.find().fetch());
    sources.push.apply(sources, Monitoring.find().fetch());
    return sources
  };

  Template.device.driverPath = function() {
    var baseurl = "https://github.com/SoftwareDefinedBuildings/smap/tree/unitoftime/python";
    var components = this.driver.split('.');
    _.each(components, function(val, idx) {
      baseurl += '/' + val
    });
    baseurl += '.py';
    return baseurl;
  };
}
