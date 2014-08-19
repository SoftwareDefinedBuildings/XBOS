
Template.schedule.master = function(){
  return MasterSchedule.findOne({});
}

Template.schedule.days = function(){
  var rv = [
    {'day': 'Sunday', 'day_id': 'sun'},
    {'day': 'Monday', 'day_id': 'mon'},
    {'day': 'Tuesday', 'day_id': 'tue'},
    {'day': 'Wednesday', 'day_id': 'wed'},
    {'day': 'Thursday', 'day_id': 'thu'},
    {'day': 'Friday', 'day_id': 'fri'},
    {'day': 'Saturday', 'day_id': 'sat'}
  ];
  return rv;
};

Template.schedule.schedules = function(){
  return Schedules.find({});
};

Template.schedule.rendered = function(){
  var master_sched = MasterSchedule.findOne({});
  _.each(master_sched, function(type, day){ 
    $('#'+day+'-schedule').val(type);
  });
};

Template.schedule.events({
  'click #save-schedule': function(){
    var master_sched = MasterSchedule.findOne({});
    var id = master_sched._id;
    _.each(master_sched, function(val, ind){
      master_sched[ind] = $('#'+ind+'-schedule').val();
    });
    delete master_sched._id;
    var r = MasterSchedule.update(id, {$set: master_sched});
    if (r == 1){
      $("#success-alert").fadeIn(800);
      window.setTimeout(function(){
        $("#success-alert").fadeOut(800);
      }, 5000);
    }
  },
  'click #add-schedule': function(){
    console.log('clicked add-schedule');
  }
});
