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
  'click #upload-floorplan': function(event, template) {
    $("#loading-gif").show();
    var file = $('#floorplan-file')[0].files[0];
    var description = $('#floorplan-description').val();
    FloorplansFS.insert(file, function (err, fileObj) {
      Floorplans.insert({"description": description, "file_id": fileObj._id});
    });
  },
  'hover .floorplan-marker': function(event){
    var room_id = $(event.target).data('room');
    var room = Rooms.find({_id: room_id}).fetch();
  }
});

function draw_markers() {
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
}

Template.building.rendered = function() {
  draw_markers();
  // make sure all images are loaded
  $(window).load(function(){
    draw_markers();
  });
  $(window).resize(function(){
    $('.floorplan-marker').remove();
    draw_markers();
  });
};

Template.building.floorplans = function() {
  return Floorplans.find({}, {reactive: false});
};
Template.add_room.floorplans = Template.building.floorplans;

Template.building.rooms = function() {
  return Rooms.find({});
};

Template.floorplan.helpers({
  getImgPath: function(){
    var fpfile = FloorplansFS.findOne({'_id': this.file_id});
    if (fpfile.hasCopy('images')){
      return '/floorplans/' + fpfile.copies.images.key;
    } else {
      return '/img/ajax-loader.gif';
    }
  }, 
});
