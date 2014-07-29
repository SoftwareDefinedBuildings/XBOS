Router.map(function() {
    this.route('home', {path: '/'});

    this.route('about');

    this.route('points');

    this.route('actuators');

    this.route('lighting');

    this.route('pointDetail', {
      path: '/points/:uuid',
      data: function() { return Points.findOne({uuid: this.params.uuid}); },
    });
});
