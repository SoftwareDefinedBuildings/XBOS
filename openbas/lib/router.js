Router.map(function() {
    this.route('dashboard', {
      path: '/',
      waitOn: function() {
        return [
          Meteor.subscribe('schedules'),
          Meteor.subscribe('master_schedule')
        ];
      },  
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
          console.log("RUNNINg");
          Meteor.call('querysystem');
          this.subscribe('Points').wait();
          this.subscribe('HVAC').wait();
          this.subscribe('Lighting').wait();
          this.subscribe('Monitoring').wait();
      },
    });
    this.route('points');
    this.route('about');
    this.route('test');

    this.route('zone_detail', {
      path: '/dashboard/:zonetype/:zone',
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

    this.route('pointDetail', {
      path: '/points/:uuid',
      data: function() { return Points.findOne({uuid: this.params.uuid}); },
    });
    
    this.route('add_schedule', {
      path: '/schedule/add',
    });
});
