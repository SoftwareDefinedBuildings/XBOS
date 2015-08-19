var ScheduleDashboard = React.createClass({
    getInitialState: function() {
        return {page: "schedule"}
    },
    render: function() {
        return (
            <div className="scheduleDashboard">
                <h1>XBOS</h1>
                <div className="row">
                    <ReactBootstrap.Nav bsStyle='tabs' activeKey={this.state.page} >
                        <ReactBootstrap.NavItem eventKey={"dashboard"} href="/">Dashboard</ReactBootstrap.NavItem>
                        <ReactBootstrap.NavItem eventKey={"schedule"} href="/schedule">Schedule</ReactBootstrap.NavItem>
                    </ReactBootstrap.Nav>
                </div>
            </div>
        )
    }
});

React.render(
    <ScheduleDashboard />,
    document.getElementById('content')
);
