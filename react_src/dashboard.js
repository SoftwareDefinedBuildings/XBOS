var queryURL = 'http://localhost:8079/api/query';

var Dashboard = React.createClass({
    getInitialState: function() {
        return {page: "dashboard", hvacZones: [], lightingZones: []};
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

        // retrieve all Lighting Zones
        $.ajax({
            url: queryURL,
            dataType: 'json',
            type: 'POST',
            data: "select distinct Metadata/LightingZone;",
            success: function(data) {
                this.setState({lightingZones: data});
            }.bind(this),
            error: function(xhr, status, err) {
                console.error(queryURL, status, err.toString());
            }.bind(this)
        });
    },
    handleSelect(selectedKey) {
        console.log('selected ' + selectedKey);
        this.setState({page: selectedKey});
    },
    render: function() {
        var contents = (<p>Loading...</p>);
        switch (this.state.page) {
        case "dashboard":
            contents = (
                <div className="row">
                    <div className='col-md-6'>
                        <HVACZoneList hvacZones={this.state.hvacZones} />
                    </div>
                    <div className='col-md-6'>
                        <LightingZoneList lightingZones={this.state.lightingZones} />
                    </div>
                </div>
            );
            break;
        case "schedule":
            contents = (
                <ScheduleList />
            );
            break;
        }

        return (
            <div className="dashboard">
            <h1>OpenBAS</h1>
            <div className="row">
                <ReactBootstrap.Nav bsStyle='tabs' activeKey={this.state.page} onSelect={this.handleSelect}>
                    <ReactBootstrap.NavItem eventKey={"dashboard"}>Dashboard</ReactBootstrap.NavItem>
                    <ReactBootstrap.NavItem eventKey={"schedule"}>Schedule</ReactBootstrap.NavItem>
                </ReactBootstrap.Nav>
            </div>
            {contents}
            </div>
        );
    }
});

React.render(
    <Dashboard />,
    document.getElementById('content')
);
