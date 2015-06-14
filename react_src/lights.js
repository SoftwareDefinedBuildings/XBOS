var LightingZoneList = React.createClass({
    render: function() {
        console.log("light zones", this.props.lightingZones);
        var zones = this.props.lightingZones.map(function(zone) {
            return (
                <LightingZone name={zone} key={zone} />
            );
        });
        return (
            <div className="lightingZoneList">
                <h2>Lighting Zones</h2>
                {zones}
            </div>
        );
    }
});

var LightingZone = React.createClass({
    render: function() {
        return (
            <div className="lightingZone">
                <h3>Zone name: {this.props.name}</h3>
                <LightingZoneRoomList zoneName={this.props.name} />
            </div>
        );
    }
});

//TODO: need lighting group list not lighting controller list

var LightingZoneRoomList = React.createClass({
    getInitialState: function() {
        return {rooms: []};
    },
    componentDidMount: function() {
        var self = this;
        run_query("select distinct Metadata/Location/Room where Metadata/LightingZone='"+this.props.zoneName+"';",
                  function(data) { //success
                    self.setState({rooms: data});
                  },
                  function(xhr, status, err) { // error
                    console.error(queryURL, status, err.toString());
                  }
        );
    },
    render: function() {
        var self = this;
        var rooms = _.map(this.state.rooms, function(roomName) {
            var queryBase = "Metadata/LightingZone='"+self.props.zoneName+"' and Metadata/Location/Room = '"+roomName+"';";
            return (
                <LightingZoneRoom key={roomName}
                                  roomName={roomName}
                                  zoneName={self.props.zoneName}
                                  queryBase={queryBase}
                />
            )
        });
        return (
            <div className="LightingZoneRoomList">
                {rooms}
            </div>
        );
    }
});

var LightingZoneRoom = React.createClass({
    getInitialState: function() {
        return({devices: []});
    },
    componentDidMount: function() {
        // map the semantic meanings to UUIDs
        var self = this;
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
            var display = ["Brightness","On","Hue","Illumination"];
            var queryBase = "Metadata/DeviceID = '"+deviceID+"'";
            return (
                <Device key={deviceID} 
                        deviceID={deviceID}
                        queryBase={queryBase}
                        display={display}/>
            )
        });
        return (
            <div className={classes}>
                  <b>Room: {self.props.roomName}</b>
                  {devices}
            </div>
        );
    }
});

var LightingController = React.createClass({
    getInitialState: function() {
        return({on: 'n/a', bri: 'n/a', sat: 'n/a'});
    },
    updateFromRepublish: function(data) {
        var timeseries_name = get_timeseries(data.Path);
        var toset = {};
        toset[timeseries_name] = get_latest_reading(data.Readings);
        this.setState(toset);
    },
    componentWillMount: function() {
        var socket = io.connect();
        var query = 'Metadata/DeviceID = "'+this.props.device._Metadata.DeviceID+'";';
        socket.emit('new subscribe', query);
        var self = this;
        socket.on(query, function(data) {
            self.updateFromRepublish(data);
        });
    },
    componentDidMount: function() {
        console.log("LightingController mounted: ", this.props.device);
    },
    render: function() {
        var cx = React.addons.classSet;
        var classes = cx({
            'well': true,
            'dark': true,
            'lightingController': true
        });
        return (
            <div className={classes}>
                <b>Lighting Controller</b>
                <p>On: {this.state.on}
                    <BinaryActuator onLabel="On" offLabel="Off" uuid={this.props.device.on.Actuator.uuid}/>
                </p>
                <p>Brightness: {this.state.bri}
                    <ContinuousActuator initialValue={this.state.bri} uuid={this.props.device.bri.Actuator.uuid} />
                </p>
                <p>Saturation: {this.state.sat}
                    <ContinuousActuator initialValue={this.state.sat} uuid={this.props.device.sat.Actuator.uuid} />
                </p>
            </div>
        );
    }
});
