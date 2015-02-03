var HVACZoneList = React.createClass({displayName: "HVACZoneList",
    render: function() {
        console.log("zones", this.props.hvacZones);
        var zones = this.props.hvacZones.map(function(zone) {
            return (
                React.createElement(HVACZone, {name: zone, key: zone})
            );
        });
        return (
            React.createElement("div", {className: "hvacZoneList"}, 
                React.createElement("h2", null, "HVAC Zones"), 
                zones
            )
        );
    }
});

var HVACZone = React.createClass({displayName: "HVACZone",
    render: function() {
        return (
            React.createElement("div", {className: "hvacZone"}, 
                React.createElement("h3", null, "Zone Name: ", this.props.name), 
                React.createElement(ThermostatList, {zoneName: this.props.name})
            )
        );
    }
});

var ThermostatList = React.createClass({displayName: "ThermostatList",
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
            return (
                React.createElement(Thermostat, {device: get_device_view(tstat_timeseries)})
            );
        });
        return (
            React.createElement("div", {className: "thermostatList"}, 
                thermostats
            )
        );
    }
});

var Thermostat = React.createClass({displayName: "Thermostat",
    getInitialState: function() {
        return({temp: 'n/a',
                temp_heat_act: 'n/a',
                temp_cool: 'n/a'});
    },
    onopen: function() {
        if (this.ws.readyState == 1) { //1 == OPEN
            this.ws.send('Metadata/DeviceID = "'+this.props.device._Metadata.DeviceID+'"');
        } else {
            this.dowstest(); // retry connection
        }
    },
    onmessage: function(msg) {
        if (msg.data.length != 0) {
            var json = $.parseJSON(msg.data);
            var path = get_timeseries(json.Path)
            if (!_.has(json,'Path')) { return; }
            var toset = {};
            toset[path] = json.Readings[0][1];
            this.setState(toset);
        }
    },
    onerror: function(e) {
        e.preventDefault();
        console.log("Error with websockets:",e);
        this.ws.close();
        this.createWS();
    },
    createWS: function(error) {
        this.ws = new WebSocket('ws://pantry.cs.berkeley.edu:8079/ws/republish');
        this.ws.onopen = this.onopen;
        this.ws.onmessage = this.onmessage;
        this.ws.onerror = this.onerror;
    },
    componentDidMount: function() {
        this.createWS();
    },
    render: function() {
        var cx = React.addons.classSet;
        var classes = cx({
            'well': true,
            'dark': true,
            'thermostat': true
        });
        return (
            React.createElement("div", {className: classes}, 
                    React.createElement("b", null, "Thermostat"), 
                    React.createElement("p", null, "Temperature: ", this.state.temp), 
                    React.createElement("p", null, "Heat Setpoint: ", this.state.temp_heat_act), 
                    React.createElement("p", null, "Cool Setpoint: ", this.state.temp_cool), 
                    React.createElement(ContinuousActuator, null), 
                    React.createElement(BinaryActuator, {onLabel: "On", offLabel: "Off"})
            )
        );
    }
});
