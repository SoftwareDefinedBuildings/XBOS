var HVACZoneList = React.createClass({
    render: function() {
        console.log("zones", this.props.hvacZones);
        var zones = this.props.hvacZones.map(function(zone) {
            return (
                <HVACZone name={zone} key={zone} />
            );
        });
        return (
            <div className="hvacZoneList">
                <h2>HVAC Zones</h2>
                {zones}
            </div>
        );
    }
});

var HVACZone = React.createClass({
    render: function() {
        return (
            <div className="hvacZone">
                <h3>Zone Name: {this.props.name}</h3>
                <HVACZoneRoomList zoneName={this.props.name} />
            </div>
        );
    }
});

var HVACZoneRoomList = React.createClass({
    getInitialState: function() {
        return {rooms: []};
    },
    componentDidMount: function() {
        // find all distinct rooms
        var self = this;
        run_query("select distinct Metadata/Location/Room where Metadata/HVAC/Zone='"+this.props.zoneName+"';",
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
            var querybase = "Metadata/HVAC/Zone='"+self.props.zoneName+"' and Metadata/Location/Room = '"+roomName+"';";
            return (
                <HVACZoneRoom key={roomName} 
                              roomName={roomName} 
                              zoneName={self.props.zoneName}
                              queryBase={querybase}
                              />
            )
        });
        return (
            <div className="HVACZoneRoomList">
                {rooms}
            </div>
        );
    }
});

//TODO: if the room we are in does not have either a heating or cooling setpoint, then we render all of the sensors together
//      and label them by their name? or what
var HVACZoneRoom = React.createClass({
    getInitialState: function() {
        return({devices: [], plotStreams: [], plotLink: "#"});
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

        // get the UUIDs for our plot points: heating/cooling setpoint and temperature
        var plotStreams = [
            {point: "Heating Setpoint", color: "#ff0000"},
            {point: "Cooling Setpoint", color: "#0000ff"},
            {point: "Temperature", color: "#000000"}
        ];
        _.each(plotStreams, function(stream, idx) {
            run_query2("select uuid where " + LOOKUP[stream.point] + " and " + self.props.queryBase,
                function(data) {
                    if (data.length == 0) { return; }
                    stream.uuid = data[0].uuid;
                    stream.name = stream.point
                    var oldps = self.state.plotStreams;
                    oldps[oldps.length] = stream;
                    self.setState({plotStreams: oldps});
                    self.updatePlotLink();
                },
                function(err) {
                    console.error("problem fetching uuid for plot", err);
                }
            )
        });
    },
    updatePlotLink: function() {
        var self = this;
        get_permalink(_.pluck(self.state.plotStreams, "uuid"), 
            function(url) {
                console.log(url);
                self.setState({plotLink: url});
            },
            function(xhr) {
                console.error(xhr);
            }
        )
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
            var display = ["Heating Setpoint", "Cooling Setpoint", "Temperature", "Humidity"];
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
                  <Plot name={self.props.roomName} length={3600} streams={this.state.plotStreams} />
                  <Button href={this.state.plotLink} bsStyle="info">Plot</Button>
                  {devices}
            </div>
        );
    }
});
