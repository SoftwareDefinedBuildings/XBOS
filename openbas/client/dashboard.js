Meteor.startup(function() {
    console.log('startup');
    // populates the HVAC and Lighting collections
    Meteor.call('querysystem');
});


if (Meteor.isClient) {

  UI.registerHelper('getValue', function(obj) {
    var p = Points.find({'uuid': this.timeseries[obj].uuid}).fetch()[0];
    return p.value;
  });

  Template.dashboard.created = function() {
    // populates the HVAC and Lighting collections
    Meteor.call('querysystem');
  };

  Template.hvacbuildingcolumn.HVACAll = function() {
    return HVAC.find({});
  };
  
  Template.lightingbuildingcolumn.LightingAll = function() {
    return Lighting.find({});
  };

}
