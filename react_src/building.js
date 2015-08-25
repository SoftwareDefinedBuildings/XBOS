// components that render informaton about the full building

var PowerMeterList = React.createClass({
    render: function() {
        var meters = _.map(this.props.powerMeters, function(meter) {
            return (
                <PowerMeter name={meter} key={meter} />
            );
        });
        return (
            <div className="powerMeterList">
                <h2>Power Meters</h2>
                {meters}
            </div>
        )
    }
});

var PowerMeter = React.createClass({
    getInitialState: function() {
        return {data: []}
    },
    componentWillMount: function() {
        //TODO: get units
        var self = this;
        run_query2("select data in (now -4h, now) as ms where Metadata/Point/Sensor = 'Power' and Metadata/Point/Type = 'Sensor' and Metadata/PowerMeter = '"+this.props.name+"';",
            function(data) {
                console.log("got data", data);
                self.setState({data: data});
                updateGraph(self.props.name, data[0].Readings);
            },
            function(err) {
                console.error("ERR fetching data", err)
            }
        )
    },
    render: function() {
        
        return (
            <div className="powerMeter">
                <p>Name: {this.props.name} </p>
                <div id={"plot"+this.props.name}>
                    <svg></svg>
                </div>
            </div>
        );
    }
});
