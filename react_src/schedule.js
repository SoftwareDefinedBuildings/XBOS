var ScheduleDashboard = React.createClass({
    getInitialState: function() {
        return {page: "schedule", viewSchedule: null}
    },
    renderSchedule: function(name) {
        this.setState({viewSchedule: name});
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
                <div className="row">
                    <div className="col-md-4">
                        <ScheduleList renderSchedule={this.renderSchedule} />
                    </div>
                    <div className="col-md-8">
                        {this.state.viewSchedule == null ? <span></span> : <ScheduleView scheduleName={this.state.viewSchedule} />}
                    </div>
                </div>
            </div>
        )
    }
});

var ScheduleView = React.createClass({
    getInitialState: function() {
        return {name: this.props.scheduleName,
                description: null,
                point_descs: {},
                periods: []}
    },
    componentDidUpdate: function(prevProps) {
        if (prevProps.scheduleName != this.props.scheduleName) {
            this.fetchSchedule();
        }
    },
    componentWillMount: function() {
        this.fetchSchedule();
    },
    fetchSchedule: function() {
        $.ajax({
            url: '/schedule/name/'+this.props.scheduleName,
            datatype: 'json',
            type: 'GET',
            success: function(schedule) {
                this.setState({description: schedule.description,
                               point_descs: schedule["point descriptions"],
                               periods: schedule.periods});
            }.bind(this),
            error: function(err) {
                console.error(err);
            }.bind(this)
        });
    },
    render: function() {
        return (
            <div className="scheduleView">
                <Panel header={"Schedule:" + this.props.scheduleName} bsStyle="info">
                    <PointDescriptionView descriptions={this.state.point_descs} />
                    <EpochListView epochs={this.state.periods} />
                </Panel>
            </div>
        )
    }
});

var PointDescriptionView = React.createClass({
    render: function() {
        var rows = _.map(this.props.descriptions, function(value, name) {
            return (
                <tr key={"row"+name}>
                    <td>{name}</td>
                    <td>{value.units}</td>
                    <td>{value.desc}</td>
                </tr>
            )
        });
        return (
            <div className="pointDescriptionView">
                <Table striped bordered condensed>
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Units</th>
                            <th>Description</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </Table>
            </div>
        );
    }

});

var EpochListView = React.createClass({
    render: function () {
        var epochs = _.map(this.props.epochs, function(epoch) {
            return (<EpochView key={epoch.name} {...epoch} />);
        });
        return (
            <div className="epochListView">
                <ListGroup>
                {epochs}
                </ListGroup>
            </div>
        )
    }
});

var EpochView = React.createClass({
    render: function() {
        var points = _.map(this.props.points, function(point) {
            return (
                <tr key={point.name}>
                    <td>{point.name}</td>
                    <td>{point.value}</td>
                </tr>
            )
        });
        var cx = React.addons.classSet;
        var classes = cx("epochView", "ListGroupItem");
        return (
            <div className={classes}>
                <div className="col-md-4">
                    <p>Name : {this.props.name}</p>
                    <p>Start : {this.props.start}</p>
                </div>
                <div className="col-md-8">
                    <Table bordered condensed>
                        <tbody>
                            {points}
                        </tbody>
                    </Table>
                </div>
            </div>
        )
    }
});

var ScheduleList = React.createClass({
    getInitialState: function() {
        return {names: []}
    },
    componentDidMount: function() {
        $.ajax({
            url: '/schedule/list',
            datatype: 'json',
            type: 'GET',
            success: function(schedules) {
                this.setState({names: schedules});
            }.bind(this),
            error: function(err) {
                console.error(err);
            }.bind(this)
        });
    },
    render: function() {
        var self = this;
        var names = _.map(this.state.names, function(name) {
            return (
                <ListGroupItem href="#" key={name} onClick={self.props.renderSchedule.bind(null, name)}>
                    {name}
                </ListGroupItem>
            )
        });
        return (
            <div className="scheduleList">
                <Panel header="Schedules">
                    <ListGroup>
                        {names}
                    </ListGroup>
                </Panel>
            </div>
        )
    }
});

React.render(
    <ScheduleDashboard />,
    document.getElementById('content')
);
