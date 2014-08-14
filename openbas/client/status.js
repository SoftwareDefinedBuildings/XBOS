if (Meteor.isClient) {

  UI.registerHelper('fixPath', function(p) {
    return p.replace(/\//g,'_');
  });

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


  Template.configuration.events({
    'click div': function(e) {
        console.log(this);
        var path = this.path;
        var fixedpath = this.path.replace(/\//g,'_');
        var query = 'select distinct where Metadata/Site = "' + Meteor.settings.public.site + '"';
        query += ' and Path~"'+path+'"';
        console.log(query);
        Meteor.call('query', query, function(err, res) {
            if (err) {
              console.log("Error running query:",query, err);
              return
            }
            if (!res) {
              console.log("No results found for",query);
              return
            }
            console.log(res);
            var rend = UI.renderWithData(Template.config_contents, res);
            UI.insert(rend, $("#device_"+fixedpath).get(0));
        });
    }
  });

  Template.contents.rendered = function() {
    $('#config_contents').append("<ul></ul>");
    var items = [];
    _.each(this.data, function(val, idx) {
      items.push('<li>'+val+'</li>');
    });
    console.log('items',items);
    $('#config_contents').append(items.join(''));
    
  };

}
