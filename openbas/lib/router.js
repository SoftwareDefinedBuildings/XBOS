Router.map(function() {
    this.route('home', {path: '/'});

    this.route('about');

    this.route('points');

    this.route('point', {
        path: '/point/:_id',
        data: function() { return Points.findOne(this.params._id); }
    });
});
