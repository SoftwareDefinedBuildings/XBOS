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
                <LightingControllerList zoneName={this.props.name} />
            </div>
        );
    }
});

var LightingControllerList = React.createClass({
    getInitialState: function() {
        return {controllers: []};
    },
    componentDidMount: function() {
        $.ajax({
            url: queryURL,
            datatype: 'json',
            type: 'POST',
            data: "select * where Metadata/LightingZone='"+this.props.zoneName+"' and Metadata/Device = 'Lighting Controller';",
            success: function(data) {
                this.setState({controllers: _.groupBy(data, function(md) {
                        return md.Metadata.DeviceID;
                    }
                )});
            }.bind(this),
            error: function(xhr, status, err) {
                console.error(queryURL, status, err.toString());
            }.bind(this)
        });
    },
    render: function() {
        console.log(this.state.controllers);
        var controllers = _.map(this.state.controllers, function(light_timeseries) {
            var view = get_device_view(light_timeseries);
            return (
                <LightingController key={view._Metadata.DeviceID} device={view} />
            );
        });
        return (
            <div className="lightingControllerList">
                {controllers}
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
