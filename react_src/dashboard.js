var Dashboard = React.createClass({
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
            <div className="dashboard">
                <h1>OpenBAS</h1>
                <HVACZoneList hvacZones={this.state.hvacZones} />
            </div>
        );
    }
});

React.render(
    <Dashboard />,
    document.getElementById('content')
);
