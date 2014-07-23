Points = new Meteor.Collection("points");

deliver = function(err, res) {
  if (err) {
    console.log(err);
  }
  console.log("got RES", res);
};

if (Meteor.isClient) {

  Template.points.pointsAll = function() {
    return Points.find({});
  };  

  Template.actuators.actuatorsAll = function() {
    // only returns points that have ActuatorPath
    return Points.find({"ActuatorUUID": {"$exists": true} })
  };

  Template.actuator_display.rendered = function() {
    var uuid = this.data.ActuatorUUID;
    console.log("rendered",uuid);
    Meteor.call('tags', uuid);
    //Meteor.call('tags', uuid, function(err, res) {
    //  if (err) {
    //    console.log("ERR:",err);
    //  }
    //  console.log("RES:", res);
    //  Session.set(uuid, res.uuid);
    //});
  };

  Template.actuator_display.type = function() {
    return Session.get(this.ActuatorUUID) || "none";
  };


  Template.navbar.helpers({
    activeIf: function (template) {
      var currentRoute = Router.current();
      return currentRoute &&
        template === currentRoute.lookupTemplate() ? 'active' : '';
    }
  });

  Template.home.greeting = function () {
    return "Welcome to openbas.";
  };

  Template.home.events({
    'click input': function () {
      // template data, if any, is available in 'this'
      if (typeof console !== 'undefined')
        console.log("You pressed the button");
    }
  });
}

if (Meteor.isServer) {
  console.log("asdf");
  console.log(Meteor.settings);
}
