var Device = React.createClass({
    getInitialState: function() {
        return({uuids: {}});
    },

    // when we mount, fetch the UUID for each display tag we are given
    componentDidMount: function() {
        var self = this;
        var state = {uuids: {}};
        _.each(this.props.display, function(displaytag) {
            self.getUUID(displaytag);
        });
        self.setState(state);
    },
    // this runs a query to retrieve the UUID for a given displaytag
    getUUID: function(displaytag) {
        var self = this;
        run_query("select uuid where "+this.props.queryBase+" and "+LOOKUP[displaytag],
                  function(data) { // success
                    var uuids = self.state.uuids;
                    uuids[data[0].uuid] = displaytag;
                    self.setState({"uuids": uuids});
                  },
                  function(xhr, status, err) { // error
                    console.error("error", displaytag, LOOKUP[displaytag]);
                    console.error(queryURL, status, err.toString());
                  });
    },
    render: function() {
        var timeseries = _.map(this.state.uuids, function(name, uuid) {
            var queryBase = "uuid = '"+uuid+"'";
            return (
                <Timeseries key={uuid} name={name} uuid={uuid} queryBase={queryBase}/>
            )
        });
        return (
            <div className="device">
                <p>DeviceID: {this.props.deviceID}</p>
                {timeseries}
            </div>
        );
    }
});


/*
 * This class wraps a UUID for a timeseries and displays both its current reading and optionally the actuator
 */
var Timeseries = React.createClass({
    mixins: [SubscribeQueryBase],
    updateFromRepublish: function(obj) {
        var self = this;
        _.map(obj, function(data) {
            self.setState({value: get_latest_reading(data.Readings)});
        });
    },
    getInitialState: function() {
        return({value: "n/a"});
    },
    componentDidMount: function() {
        var self = this;
        run_query("select * where uuid = '"+this.props.uuid+"'",
                  function(data) { // success
                    self.setState(data[0])
                  },
                  function(xhr, status, err) { // error
                    console.error("error", displaytag, LOOKUP[displaytag]);
                    console.error(queryURL, status, err.toString());
                  });
    },
    render: function() {
        var act = (<p></p>);
        if (this.state.Actuator != undefined) {
            act = (<Actuator ActuatorUUID={this.state.Actuator.uuid}/>);
        }
        var cx = React.addons.classSet;
        var classes = cx({
            'box': true,
            'timeseries': true
        });
        return (
            <div className={classes}>
                <b>TIMESERIES</b>
                <p>ts uuid: {this.props.uuid} </p>
                <p>{this.props.name}: {this.state.value}</p>
                {act}
            </div>
        )
    }
});
