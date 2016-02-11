var SensorRoomList = React.createClass({
    render: function() {
        console.log("sensor list", this.props.roomList);
        var rooms = this.props.roomList.map(function(room) {
            var queryBase = "Metadata/Location/Room='"+room+"' and Metadata/Point/Type='Sensor'";
            return (
                <SensorRoom name={room} key={room} queryBase={queryBase} />
            );
        });
        return (
            <div className="sensorRoomList">
                <h2>Sensors</h2>
                {rooms}
            </div>
        );
    }
});

var SensorRoom = React.createClass({
    getInitialState: function() {
        return({devices: [], plotStreams: []});
    },

    componentDidMount: function() {
        // map the semantic meanings to UUIDs
        var self = this;
        console.log("sensor query","select distinct Metadata/DeviceID where "+self.props.queryBase)
        run_query("select distinct Metadata/DeviceID where "+self.props.queryBase,
                  function(data) { //success
                    self.setState({devices: data})
                  },
                  function(xhr, status, err) { // error
                    console.error(queryURL, status, err.toString());
                  }
        );
    },

    render: function() {
        var cx = React.addons.classSet;
        var classes = cx({
            'well': true,
            'dark': true,
            'HVACZoneRoom': true
        });
        var self = this;
        var devices = _.map(this.state.devices, function(deviceID) {
            var display = ["Temperature","Occupancy"];
            var queryBase = "Metadata/DeviceID = '"+deviceID+"'";
            return (
                <Device key={deviceID} 
                        deviceID={deviceID}
                        queryBase={queryBase}
                        display={display}/>
            )
        });
        return (
            <div className="sensorRoom">
                <h3>Room: {this.props.name}</h3>
                {devices}
            </div>
        )
    }
});
