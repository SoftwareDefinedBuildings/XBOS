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
            </div>
        );
    }
});
