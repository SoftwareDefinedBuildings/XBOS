Router.map(function() {
    this.route('dashboard', {path: '/'});
    this.route('schedule');
    this.route('status');
    this.route('points');
    this.route('actuators');
    this.route('lighting');
    this.route('hvac');
    this.route('about');
    this.route('test');

    this.route('pointDetail', {
      path: '/points/:uuid',
      data: function() { return Points.findOne({uuid: this.params.uuid}); },
    });
});
