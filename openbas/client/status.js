if (Meteor.isClient) {

  Template.status.sources = function () {
    /*
     * Grabs all the HVAC, Lighting and Monitoring points. These 
     * have been configured, so we can read their metadata. Thanks
     * to the 'querysystem' function, thse are pre-aggregated by
     * their driver path instead of the individual timeseries
     */
    var sources = [];
    sources.push.apply(sources, HVAC.find().fetch());
    sources.push.apply(sources, Lighting.find().fetch());
    sources.push.apply(sources, Monitoring.find().fetch());
    return sources
  };

  Template.device.driverPath = function() {
    /*
     * From the driver module path (e.g. smap.drivers.lights.VirtualLightDriver),
     * we generate the URL to the code of the driver
     */
    var baseurl = "https://github.com/SoftwareDefinedBuildings/smap/tree/unitoftime/python";
    var components = this.driver.split('.');
    _.each(components, function(val, idx) {
      baseurl += '/' + val
    });
    baseurl += '.py';
    return baseurl;
  };
}
