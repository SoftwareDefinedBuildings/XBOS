Points = new Meteor.Collection("points");
Rooms = new Meteor.Collection("rooms");
HVAC = new Meteor.Collection("hvac");
Lighting = new Meteor.Collection("lighting");
Monitoring = new Meteor.Collection("monitoring");
GeneralControl = new Meteor.Collection("general_control");
Schedules = new Meteor.Collection("schedules");
MasterSchedule = new Meteor.Collection("master_schedule");
Unconfigured = new Meteor.Collection("unconfigured");
Floorplans = new Meteor.Collection("floorplans");
Site = new Meteor.Collection("site");

if (Meteor.isServer) {

  if (Schedules.find({}).fetch().length == 0){
    var schedules = EJSON.parse(Assets.getText("schedules.json"));
    _.each(schedules, function(s){
      Schedules.insert(s);
    });
  }

  if (MasterSchedule.find({}).fetch().length == 0){
    MasterSchedule.insert({
      'mon': 'weekday',
      'tue': 'weekday',
      'wed': 'weekday',
      'thu': 'weekday',
      'fri': 'weekday',
      'sat': 'weekend',
      'sun': 'weekend',
    });
  }
 
  if (Rooms.find({}).fetch().length == 0){
    var rooms = EJSON.parse(Assets.getText(Meteor.settings.roomsfile));
    _.each(rooms, function(r){
      Rooms.insert(r);
    });
  }

  Meteor.publish("master_schedule", function () {
    return MasterSchedule.find({});
  });
  Meteor.publish("schedules", function () {
    return Schedules.find({});
  });
  Meteor.publish("hvac", function () {
    return HVAC.find({});
  });
  Meteor.publish("lighting", function () {
    return Lighting.find({});
  });
  Meteor.publish("points", function () {
    return Points.find({});
  });
  Meteor.publish("monitoring", function () {
    return Monitoring.find({});
  });
  Meteor.publish("unconfigured", function () {
    return Unconfigured.find({});
  });
  Meteor.publish("site", function () {
    return Site.find({});
  });

}

Meteor.startup(function(){
  if (Meteor.isServer){

    // add default admin user (default password in settings)
    if (!Meteor.users.find().count()){
      var user = {
        username: 'admin',
        password: Meteor.settings.default_password,
      };
      Accounts.createUser(user); 
    }

    Accounts.config({
      forbidClientAccountCreation: true
    });

    Accounts.onLogin(function(){
      Router.go('/'); 
    });

    Meteor.settings.public.project_root = process.env.PWD;

  };

  FloorplansFS = new FS.Collection("floorplans_fs", {
    stores: [new FS.Store.FileSystem("images", {path: Meteor.settings.public.project_root + "/public/floorplans"})]
  });

  Site.upsert({'_id':'Site'},{'_id': 'Site', 'Site': Meteor.settings.public.site});
});
