// components that render informaton about the full building

var PowerMeterList = React.createClass({
    render: function() {
        var meters = _.map(this.props.powerMeters, function(meter) {
            var queryBase = "Metadata/Point/Sensor = 'Power' and Metadata/Point/Type = 'Sensor' and Metadata/PowerMeter = '"+meter+"';"
            return (
                <PowerMeter name={meter} key={meter} queryBase={queryBase} />
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
    mixins: [SubscribeQueryBase],
    updateFromRepublish: function(obj) {
        var self = this;
        _.map(obj, function(data) {
            self.setState({lastValue: get_latest_reading(data.Readings).toFixed(2),
                           lastTime: get_latest_timestamp(data.Readings)*1000});
        });
    },
    getInitialState: function() {
        return {data: [], units: "n/a", lastValue: null, lastTime: null}
    },
    componentWillMount: function() {
        //TODO: get units
        var self = this;
        run_query2("select Properties/UnitofMeasure where " + self.props.queryBase,
            function(data) {
                self.setState({units: data[0].Properties.UnitofMeasure});
                run_query2("select data in (now -4h, now) as ms where " + self.props.queryBase,
                    function(data) {
                        self.setState({data: data});
                        var readings = data[0].Readings;
                        updateGraph(self.props.name, self.state.units, readings);
                        self.setState({lastReading: readings[readings.length-1] });
                    },
                    function(err) {
                        console.error("ERR fetching data", err)
                    }
                )
            },
            function(err) {
                console.error("ERR fetching data", err)
            }
        )
    },
    render: function() {
        return (
            <div className="powerMeter">
                <p>Power Meter: {this.props.name} </p>
                <p>Current Value: {this.state.lastValue} {this.state.units} at {moment(this.state.lastTime).format("D MMM hh:mm:ss A")} </p>
                <div id={"plot"+this.props.name}>
                    <svg></svg>
                </div>
            </div>
        );
    }
});
