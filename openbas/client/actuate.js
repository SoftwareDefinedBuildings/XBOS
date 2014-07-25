if (Meteor.isClient) {
  var actuators = {};
  var actuatorsDep = new Deps.Dependency;

  var getActuators = function(act_uuid) {
    actuatorsDep.depend();
    return actuators[act_uuid] || {"Actuator": {"Model": "none", "States": [0,1], "MinValue": 0, "MaxValue": 100}};
  };

  var updateActuators = function(act_uuid, data) {
    actuators[act_uuid] = data;
    actuatorsDep.changed();
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
    return getActuators(this.ActuatorUUID).Actuator.Model || "none";
  };

  // functions to help determine type of actuator based on Actuator.Model from sMAP metadata
  Template.actuator_display.helpers({
    isDiscrete: function(template) {
      return getActuators(this.ActuatorUUID).Actuator.Model === "discrete";
    },
    isBinary: function(template) {
      return getActuators(this.ActuatorUUID).Actuator.Model === "binary";
    },
    isContinuous: function(template) {
      return getActuators(this.ActuatorUUID).Actuator.Model === "continuous";
    }
  });

  Template.actuator_continuous.rendered = function() {
    if (Meteor.isClient) {
      var that = getActuators(this.data.ActuatorUUID);
      var port = this.data.ServerPort;
      $("#"+this.data.ActuatorUUID).slider({
        min: 100*that.Actuator.MinValue,
        max: that.Actuator.MaxValue,
        step: 1,
        value: this.data.value
      }).on('slideStop', function(e) {
        Meteor.call("actuate", port, that.Path, e.value, function(err, res) {
          if (err) {
            console.log("ERROR", err);
          }
        });
      });
    }
  };

  Template.actuator_continuous.value = function() {
    if (Meteor.isClient) {
      var p = Points.find({'_id': this._id}).fetch();
      $('#'+this.ActuatorUUID).slider('setValue', p[0].value);
      return p[0].value;
    }
  };

  Template.actuator_discrete.rendered = function() {
    if (Meteor.isClient) {
      that = getActuators(this.data.ActuatorUUID);
    }
  };

  Template.actuator_binary.rendered = function() {
    if (Meteor.isClient) {
      var that = getActuators(this.data.ActuatorUUID);
    }
  };

  Template.actuator_binary.value = function() {
    if (Meteor.isClient) {
      var p = Points.find({'_id': this._id}).fetch();
      if (p[0].value === 0) {
        $('#'+this.ActuatorUUID).removeClass("pressed");
      } else {
        $('#'+this.ActuatorUUID).addClass("pressed");
      }
      return p[0].value;
    }
  };


  Template.actuator_binary.events({
    'click a': function () {
      if (this.value === 1) {
        $('#'+this.ActuatorUUID).removeClass("pressed");
        var act = getActuators(this.ActuatorUUID);
        Meteor.call("actuate", this.ServerPort, act.Path, "0", function(err, res) {
          if (err) {
            console.log("ERROR", err);
          }
          console.log("RES",res);
        });
      } else {
        var act = getActuators(this.ActuatorUUID);
        Meteor.call("actuate", this.ServerPort, act.Path, "1", function(err, res) {
          if (err) {
            console.log("ERROR", err);
          }
          console.log("RES",res);
        });
        $('#'+this.ActuatorUUID).addClass("pressed");
      }
    }
  });



}
