Template.add_room.events({
  'click #save-room': function(){ 
    var r = {
      'RoomNumber': $("#room-number").val(),
      'Description': $("#room-description").val(),
      'HVACZone': $("#hvac-zone").val(),
      'LightingZone': $("#lighting-zone").val(),
      'Exposure': $("#exposure").val()
    };
    Rooms.insert(r);
    window.location.href = '/building/';
  },
  'click #cancel-room': function(){ 
    window.location.href = '/building/';
  },
});

Template.building.floorplans = function() {
  return Floorplans.find({});
};

Template.building.rooms = function() {
  return Rooms.find({});
};
