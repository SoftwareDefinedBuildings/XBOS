if (Meteor.isClient) {

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

  Template.schedule.blurb = function () {
    return "Build and Manipulate the weekly schedule";
  };


  Template.test.greeting = function () {
    return "Welcome to openbas.";
  };

  Template.test.events({
    'click input': function () {
      // template data, if any, is available in 'this'
      if (typeof console !== 'undefined')
        console.log("You pressed the button");
    }
  });
}
