var republishURL = "http://pantry.cs.berkeley.edu:8079/ws/republish";
var queryURL = "http://pantry.cs.berkeley.edu:8079/api/query"
var Dashboard = React.createClass({displayName: "Dashboard",
    getInitialState: function() {
        return {hvacZones: []};
    },
    componentDidMount: function() {
        // retrieve all HVAC zones
        $.ajax({
            url: queryURL,
            dataType: 'json',
            type: 'POST',
            data: "select distinct Metadata/HVACZone;",
            success: function(data) {
                this.setState({hvacZones: data});
            }.bind(this),
            error: function(xhr, status, err) {
                console.error(queryURL, status, err.toString());
            }.bind(this)
        });
    },
    render: function() {
        return (
            React.createElement("div", {className: "dashboard"}, 
                React.createElement("h1", null, "OpenBAS"), 
                React.createElement(HVACZoneList, {hvacZones: this.state.hvacZones})
            )
        );
    }
});

React.render(
    React.createElement(Dashboard, null),
    document.getElementById('content')
);
