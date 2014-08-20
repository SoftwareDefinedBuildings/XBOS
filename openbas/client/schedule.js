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
    if (r){
      $("#success-alert").slideDown(800);
      window.setTimeout(function(){
        $("#success-alert").slideUp(800);
      }, 5000);
    }
  },
});

Template.edit_schedule.events({
  'click .add-control-point': function(){
    var row = '<tr class="period-point"><td><input type="text" class="period-point-path form-control"></td>'
            + '<td><input type="text" class="period-point-value form-control"></td></tr>';
    $("#schedule-period-" + this.name).append(row);
  },
  'click #edit-schedule-save': function(){
    var id = this._id;
    var periods = _.map($('.schedule-period'), function(p){
      rv = {};
      rv.name = $(p).find(".period-name").val();
      rv.start = $(p).find(".period-start").val();
      rv.points = _.map($(p).find(".period-point"), function(point){
        mypoint = {};
        mypoint.path = $(point).find('.period-point-path').val();
        mypoint.value = $(point).find('.period-point-value').val();
        return mypoint;
      });
      return rv; 
    });
    this.periods = periods;
    this.name = $('#schedule-name').val();
    delete this._id;

    var r = Schedules.update(id, {$set: this});
    if (r){
      $("#success-alert").slideDown(800);
      window.setTimeout(function(){
        $("#success-alert").slideUp(800);
      }, 5000);
    }
  }
});

Template.add_schedule.events({
  'click #add-period': function(event){
    var rendered = UI.render(Template.schedule_period);
    UI.insert(rendered, $('table')[0]);
  },
  'click .add-control-point': function(event){
    var period_id = $(event.target).data('period');
    var row = '<tr class="period-point"><td><input type="text" class="period-point-path form-control"></td>'
            + '<td><input type="text" class="period-point-value form-control"></td></tr>';
    $("#schedule-period-" + period_id).append(row);
  },
  'click #add-schedule-save': function(){
    console.log('clicked add-schedule-save');
  }
});


