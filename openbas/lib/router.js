Router.map(function() {
    this.route('dashboard', {path: '/'});
    this.route('schedule');
    this.route('status');
    this.route('points');
    this.route('about');
    this.route('test');

    this.route('zone_detail', {
      path: '/dashboard/:zonetype/:zone',
      data: function() { 
        console.log(this.params.zone);
        if (this.params.zonetype == 'hvac') {
          return {'type': 'hvac', 'points': HVAC.find({'zone': this.params.zone}).fetch()};
        } else if (this.params.zonetype == 'lighting') {
          return {'type': 'lighting', 'points': Lighting.find({'zone': this.params.zone}).fetch()};;
        } else {
          return 0
        }
      }
    });

    this.route('pointDetail', {
      path: '/points/:uuid',
      data: function() { return Points.findOne({uuid: this.params.uuid}); },
    });
});
