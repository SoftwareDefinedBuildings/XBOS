Router.map(function() {
    this.route('dashboard', {
      path: '/',
      waitOn: function() {
        return [
          Meteor.subscribe('schedules'),
          Meteor.subscribe('master_schedule'),
          Meteor.subscribe('points'),
          Meteor.subscribe('hvac'),
          Meteor.subscribe('lighting'),
          Meteor.subscribe('monitoring')
        ];
      },  
      action: function () {
        if (this.ready()){ 
          this.render();
        } else {
            this.render('loading');
        } 
      }
    });

    this.route('schedule', {
      waitOn: function(){
        return [
          Meteor.subscribe('schedules'),
          Meteor.subscribe('master_schedule')
        ];
      },
    });
    
    this.route('status', {
      onBeforeAction: function() {
        Meteor.call('querysystem');
        this.subscribe('hvac').wait();
        this.subscribe('monitoring').wait();
        this.subscribe('lighting').wait();
        this.subscribe('points').wait();
        this.subscribe('unconfigured').wait();
        this.subscribe('site').wait();
      },
    });

    this.route('points');
    this.route('about');
    this.route('plot');
    
    this.route('zone_detail', {
      path: '/dashboard/:zonetype/:zone',
      waitOn: function() {
        return [
          Meteor.subscribe('points'),
          Meteor.subscribe('hvac'),
          Meteor.subscribe('lighting'),
          Meteor.subscribe('monitoring')
        ];
      },
      data: function() { 
        console.log(this.params.zone);
        if (this.params.zonetype == 'hvac') {
          return {'type': 'hvac', 'points': HVAC.find({'hvaczone': this.params.zone}).fetch()};
        } else if (this.params.zonetype == 'lighting') {
          return {'type': 'lighting', 'points': Lighting.find({'lightingzone': this.params.zone}).fetch()};;
        } else {
          return 0
        }
      }
    });

    this.route('room_detail', {
      path: '/room/:room',
      data: function(){
        return {'room': this.params.room, 'points': GeneralControl.find({'room': this.params.room}) };
      }
    });

    this.route('pointDetail', {
      path: '/points/:uuid',
      data: function() { return Points.findOne({uuid: this.params.uuid}); },
    });
    
    this.route('view_schedule', {
      path: '/schedule/view/:id',
      data: function() { return Schedules.findOne({_id: this.params.id}); },
    });
    
    this.route('edit_schedule', {
      path: '/schedule/edit/:id',
      data: function() { return Schedules.findOne({_id: this.params.id}); },
    });
    
    this.route('add_schedule', {
      path: '/schedule/add',
      data: {'iperiod': 0},
    });

    this.route('building', {
      waitOn: function(){
        return [Meteor.subscribe("rooms"), Meteor.subscribe("floorplans")];
      },
    });

    this.route('add_room', {
      path: '/building/add_room', 
      waitOn: function(){
        return [Meteor.subscribe("rooms"), Meteor.subscribe("floorplans")];
      }
    });
});
