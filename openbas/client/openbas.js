OpenBAS = {};

OpenBAS.PathNames = [
  {"path": "temp_heat", "name": "Heating setpoint"},
  {"path": "temp_cool", "name": "Cooling setpoint"},
  {"path": "hvac_state", "name": "HVAC state"},
  {"path": "on", "name": "Lights"},
];

Template.points.pointsAll = function() {
  return Points.find({});
};

Template.points.helpers({
  notActuator: function(template){
    var re = /.*_act$/;
    var result = re.exec(this.Path);
    return result == null;
  }
});

Template.point_row.value_fmt = function() {
  var val = this.value
  if ((String(val).split('.')[1] || []).length > 2){
    return this.value.toFixed(2);
  } else {
    return this.value;
  } 
}

Template.navbar.building_name = function() {
   return Meteor.settings.public.building_name;
};

Template.navbar.helpers({
  activeIf: function (template) {
    var currentRoute = Router.current();
    return currentRoute &&
      template === currentRoute.lookupTemplate() ? 'active' : '';
  },
});
