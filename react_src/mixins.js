// This mixin uses the self.props.queryBase as a where clause for a query that helps all further queries get
// funneled down into being just for this component. It opens a websocket connection and calls updateFromRepublish
// for each data point returned
var SubscribeQueryBase = {
    componentWillMount: function() {
        console.log("Starting subscription for", this.props.queryBase);
        this.socket = io.connect();
        this.socket.emit('new subscribe', this.props.queryBase);
        var self = this;
        this.socket.on(this.props.queryBase, function(data) {
            if (self.isMounted()) {
                self.updateFromRepublish(data);
            }
        });
    },
    componentWillUnmount() {
        this.socket.disconnect();
    }
};
