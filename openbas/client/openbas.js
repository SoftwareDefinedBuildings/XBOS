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
