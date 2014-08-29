Template.add_room.events({
  'click #save-room': function(){ 
    var marker = $(".floorplan-marker");
    var image = marker.siblings('img');
    var floorplan_id = image.attr('id');
    var img_position_abs = image.position();
    var marker_position_abs = marker.position();
    var marker_position_rel = {
      'top': marker_position_abs.top - img_position_abs.top,
      'left': marker_position_abs.left - img_position_abs.left
    };
    var r = {
      'RoomNumber': $("#room-number").val(),
      'Description': $("#room-description").val(),
      'HVACZone': $("#hvac-zone").val(),
      'LightingZone': $("#lighting-zone").val(),
      'Exposure': $("#exposure").val(),
      'FloorplanId': floorplan_id,
      'MarkerPosition': marker_position_rel,
    };
    Rooms.insert(r);
    Router.go('/building/');
  },
  'click #cancel-room': function(){ 
    Router.go('/building/');
  },
  'click .floorplan': function(event){
    $('.floorplan-marker').remove();
    var offsetX = -15;
    var offsetY = -31;
    var markerX = event.pageX + offsetX;
    var markerY = event.pageY + offsetY;
    var marker = $('<span />')
        .attr('class', 'floorplan-marker glyphicon glyphicon-map-marker')
        .attr('display', 'none')
        .css('left', markerX + "px")
        .css('top', markerY + "px");

    $(event.target).parent('div').append(marker);

    jQuery({count: 100}).animate({count: 0},{
      duration: 1000,
      step: function(){
        marker.css('top', markerY - this.count)
      },
      easing: 'easeOutBounce',
    });
  },
});

Template.building.events({
  'hover .floorplan-marker': function(event){
    var room_id = $(event.target).data('room');
    var room = Rooms.find({_id: room_id}).fetch();
  }
});

Template.building.rendered = function() {
  var rooms = Rooms.find({}).fetch();
  _.each(rooms, function(room){
    if (room.hasOwnProperty('MarkerPosition')){
      var img_pos = $('img#' + room.FloorplanId).position();
      var marker = $('<span />')
          .attr('title', room.RoomNumber)
          .attr('class', 'floorplan-marker floorplan-marker-static glyphicon glyphicon-map-marker')
          .attr('data-room', room._id)
          .css('left', img_pos.left + room.MarkerPosition.left + "px")
          .css('top', img_pos.top + room.MarkerPosition.top + "px");
      $('div#floorplan-' + room.FloorplanId).append(marker);
    }
  });
  $(".floorplan-marker").tooltip({
    placement: "top",
  });
};

Template.building.floorplans = function() {
  return Floorplans.find({});
};
Template.add_room.floorplans = Template.building.floorplans;

Template.building.rooms = function() {
  return Rooms.find({});
};

Template.upload.events({
  'change .fileUploader': function(event, template) {
    var files = event.target.files;
    for (var i = 0, ln = files.length; i < ln; i++) {
      Images.insert(files[i], function (err, fileObj) {
        console.log('Inserted new doc with ID fileObj._id, and kicked off the data upload using HTTP');
      });
    }
  }
});
