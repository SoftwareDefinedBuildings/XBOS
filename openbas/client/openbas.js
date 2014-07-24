Points = new Meteor.Collection("points");

if (Meteor.isClient) {

  var actuators = {};
  var actuatorsDep = new Deps.Dependency;

  var getActuators = function(act_uuid) {
    actuatorsDep.depend();
    return actuators[act_uuid] || {"Actuate": {"Model": "none", "States": [0,1]}};
  };

  var updateActuators = function(act_uuid, data) {
    actuators[act_uuid] = data;
    actuatorsDep.changed();
  };

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
      updateActuators(res[0].uuid, res[0]);
    });
  };

  Template.actuator_display.type = function() {
    return getActuators(this.ActuatorUUID).Actuate.Model || "none";
  };

  // functions to help determine type of actuator based on Actuate.Model from sMAP metadata
  Template.actuator_display.helpers({
    isDiscrete: function(template) {
      return getActuators(this.ActuatorUUID).Actuate.Model === "discrete";
    },
    isBinary: function(template) {
      return getActuators(this.ActuatorUUID).Actuate.Model === "binary";
    },
    isContinuous: function(template) {
      return getActuators(this.ActuatorUUID).Actuate.Model === "continuous";
    }
  });

  Template.actuator_continuous.rendered = function() {
    if (Meteor.isClient) {
      that = getActuators(this.data.ActuatorUUID);
      $("#"+this.data.ActuatorUUID).slider({
        min: that.Actuate.States[0],
        max: that.Actuate.States[1],
        value: this.data.value
      });
    }
  };

  Template.actuator_binary.events({
    'click a': function () {
      console.log(this);
      if (this.value === 1) {
        this.value = 0;
        $('#'+this.ActuatorUUID).removeClass("pressed");
      } else {
        this.value = 1;
        $('#'+this.ActuatorUUID).addClass("pressed");
      }
      console.log("clicked a button", this);
    }
  });


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
