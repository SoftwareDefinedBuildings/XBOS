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

Template.navbar.helpers({
  activeIf: function (template) {
    var currentRoute = Router.current();
    return currentRoute &&
      template === currentRoute.lookupTemplate() ? 'active' : '';
  }
});
