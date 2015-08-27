var queryURL = 'http://pantry.cs.berkeley.edu:8079/api/query';

var Dashboard = React.createClass({
    getInitialState: function() {
        return {page: "dashboard", hvacZones: [], lightingZones: [], powerMeters: []};
    },
    componentDidMount: function() {
        var self = this;
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

        // retrieve full building power to render
        run_query2("select distinct Metadata/PowerMeter;",
            function(data) {
                self.setState({powerMeters: data});
            },
            function(err) {
                console.error("NOPE!", err);
            }
        )
    },
    render: function() {
        return (
            <div className="dashboard">
            <h1>XBOS</h1>
            <div className="row">
                <ReactBootstrap.Nav bsStyle='tabs' activeKey={this.state.page} >
                    <ReactBootstrap.NavItem eventKey={"dashboard"} href="/dashboard">Dashboard</ReactBootstrap.NavItem>
                    <ReactBootstrap.NavItem eventKey={"schedule"} href="/schedule">Schedule</ReactBootstrap.NavItem>
                    <ReactBootstrap.NavItem eventKey={"status"} href="/deckard"><Glyphicon glyph="chevron-right" /> Status</ReactBootstrap.NavItem>
                    <ReactBootstrap.NavItem eventKey={"plotter"} href="/plotter"><Glyphicon glyph="chevron-right" /> Plotter</ReactBootstrap.NavItem>
                </ReactBootstrap.Nav>
            </div>
            <div className="row">
                <div className='col-md-4'>
                    <h2>Building Info</h2>
                    <PowerMeterList powerMeters={this.state.powerMeters} />
                </div>
                <div className='col-md-4'>
                    <HVACZoneList hvacZones={this.state.hvacZones} />
                </div>
                <div className='col-md-4'>
                    <LightingZoneList lightingZones={this.state.lightingZones} />
                </div>
            </div>
            </div>
        );
    }
});

React.render(
    <Dashboard />,
    document.getElementById('content')
);
