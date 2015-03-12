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
                <ThermostatList zoneName={this.props.name} />
            </div>
        );
    }
});

var ThermostatList = React.createClass({
    getInitialState: function() {
        return {thermostats: []};
    },
    componentDidMount: function() {
        $.ajax({
            url: queryURL,
            datatype: 'json',
            type: 'POST',
            data: "select * where Metadata/HVACZone='"+this.props.zoneName+"' and Metadata/Device = 'Thermostat';",
            success: function(data) {
                this.setState({thermostats: _.groupBy(data, function(md) {
                        return md.DeviceID;
                    }
                )});
            }.bind(this),
            error: function(xhr, status, err) {
                console.error(queryURL, status, err.toString());
            }.bind(this)
        });
    },
    render: function() {
        var thermostats = _.map(this.state.thermostats, function(tstat_timeseries) {
            var view = get_device_view(tstat_timeseries);
            return (
                <Thermostat key={view._Metadata.DeviceID} device={view}/>
            );
        });
        return (
            <div className="thermostatList">
                {thermostats}
            </div>
        );
    }
});

var Thermostat = React.createClass({
    getInitialState: function() {
        return({temp: 'n/a',
                temp_heat: 'n/a',
                temp_cool: 'n/a'});
    },
    updateFromRepublish: function(data) {
        var timeseries_name = get_timeseries(data.Path);
        var toset = {};
        toset[timeseries_name] = get_latest_reading(data.Readings);
        this.setState(toset);
    },
    componentWillMount: function() {
        var socket = io.connect();
        var query = 'Metadata/HVACZone = "'+this.props.device._Metadata.HVACZone+'";';
        socket.emit('new subscribe', query);
        var self = this;
        socket.on(query, function(data) {
            self.updateFromRepublish(data);
        });
    },
    componentDidMount: function() {
        console.log("Thermostat mounted: ", this.props.device);
    },
    render: function() {
        var cx = React.addons.classSet;
        var classes = cx({
            'well': true,
            'dark': true,
            'thermostat': true
        });
        return (
            <div className={classes}>
                    <b>Thermostat</b>
                    <p>Temperature: {this.state.temp}</p>
                    <p>Heat Setpoint: {this.state.temp_heat} 
                        <ContinuousActuator initialValue={this.state.temp_heat} 
                                            uuid={this.props.device.temp_heat.Actuator.uuid} />
                    </p>
                    <p>Cool Setpoint: {this.state.temp_cool} 
                        <ContinuousActuator initialValue={this.state.temp_cool}
                                            uuid={this.props.device.temp_cool.Actuator.uuid} />
                    </p>
                    <p>Override: {this.state.override} 
                        <BinaryActuator onLabel="On" offLabel="Off" uuid={this.props.device.override.Actuator.uuid}/>
                    </p>
            </div>
        );
    }
});
