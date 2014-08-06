Points = new Meteor.Collection("points");
Rooms = new Meteor.Collection("rooms");
HVAC = new Meteor.Collection("hvac");
Lighting = new Meteor.Collection("lighting");
Monitoring = new Meteor.Collection("monitoring");

if (Meteor.isServer) {

  if (Rooms.find({}).fetch().length == 0){
    var rooms = EJSON.parse(Assets.getText("rooms.json"));
    _.each(rooms, function(r){
      Rooms.insert(r);
    });
  }

}
