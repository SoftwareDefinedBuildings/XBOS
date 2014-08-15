Points = new Meteor.Collection("points");
Rooms = new Meteor.Collection("rooms");
HVAC = new Meteor.Collection("hvac");
Lighting = new Meteor.Collection("lighting");
Monitoring = new Meteor.Collection("monitoring");
Schedules = new Meteor.Collection("schedules");

if (Meteor.isServer) {

  if (Schedules.find({}).fetch().length == 0){
    var schedules = EJSON.parse(Assets.getText("schedules.json"));
    _.each(schedules, function(s){
      Schedules.insert(s);
    });
  }

  if (Rooms.find({}).fetch().length == 0){
    var rooms = EJSON.parse(Assets.getText("rooms.json"));
    _.each(rooms, function(r){
      Rooms.insert(r);
    });
  }

}
