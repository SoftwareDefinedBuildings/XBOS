Points = new Meteor.Collection("points");

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
    Meteor.call('tags', uuid, function(err, res) {
      if (err) {
        console.log(err);
      }
      Session.set(res[0].uuid, res[0].Actuate.Model);
    });
  };

  Template.actuator_display.type = function() {
    return Session.get(this.ActuatorUUID) || "none";
  };

  // functions to help determine type of actuator based on Actuate.Model from sMAP metadata
  Template.actuator_display.helpers({
    isDiscrete: function(template) {
      return Session.get(this.ActuatorUUID) === "discrete";
    },
    isBinary: function(template) {
      return Session.get(this.ActuatorUUID) === "binary";
    },
    isContinuous: function(template) {
      return Session.get(this.ActuatorUUID) === "continuous";
    }
  });

  Template.actuator_continuous.rendered = function() {
    if (Meteor.isClient) {
      //TODO: write methods to get min/max from the sMAP metadata and use that o create the slider
      console.log(this.data.ActuatorUUID);
      $("#"+this.data.ActuatorUUID).slider({
      });
    }
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
}
