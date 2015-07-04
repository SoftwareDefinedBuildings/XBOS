var ScheduleList = React.createClass({
    getInitialState: function() {
        return {schedules: [], editing: null, viewing: null};
    },
    componentDidMount: function() {
        /*
         * When we mount this component, query the server to get a list of names of
         * available schedules
         */
        $.ajax({
            url: '/schedule/list',
            dataType: 'json',
            type: 'GET',
            success: function(data) {
                this.setState({schedules: data});
            }.bind(this),
            error: function(xhr, status, err) {
                console.error(status, err.toString());
            }.bind(this)
        });
    },
    editSchedule: function(schedulename) {
        this.setState({editing: schedulename, viewing: null});
    },
    render: function() {
        /*
         * Our schedule view is 2 columns. The leftmost is a thin column of <ScheduleHead> that lists
         * the schedule and provides a View and Edit button. We link our own {edit,view}Schedule methods
         * to each of the rendered ScheduleHead components so that we know which schedule was clicked for
         * viewing/editing
         */
        var ListGroupItem = ReactBootstrap.ListGroupItem;
        var schedules = this.state.schedules.map(function(schedulename) {
            var boundClick = this.editSchedule.bind(this, schedulename);
            return (
                <ListGroupItem key={schedulename} name={schedulename} onClick={boundClick}>
                    {schedulename}
                </ListGroupItem>
            );
        }, this);
        var cx = React.addons.classSet;
        var left_classes = cx({
            'well': true,
            'col-md-4': true
        });

        var right_cx = React.addons.classSet;
        var right_classes = right_cx({
            'well': true,
            'col-md-8': true
        });
        var render_right = (<div></div>);
        if (this.state.editing != null) {
            console.log("rdner right");
            render_right = <ScheduleEditor key={this.state.editing} name={this.state.editing}/>
        }
        var ListGroup = ReactBootstrap.ListGroup;
        return (
            <div className="scheduleList">
                <div className="row">
                    <div className={left_classes}>
                        <h2>Schedule List</h2>
                        <ListGroup>
                            {schedules}
                        </ListGroup>
                    </div>
                    <div className={right_classes}>
                        {render_right}
                    </div>
                </div>
            </div>
        );
    }
});

var ScheduleEditor = React.createClass({
    getInitialState: function() {
        return {};
    },
    componentWillMount: function() {
        $.ajax({
            url: '/schedule/'+this.props.name.name,
            dataType: 'json',
            type: 'GET',
            success: function(data) {
                console.log("recv",data);
                this.setState(data)
            }.bind(this),
            error: function(xhr, status, err) {
                console.error(status, err.toString());
            }.bind(this)
        });
    },
    handleChange: function(event) {
        console.log("got event", event);
        this.props.onChange(this.props.name, "value");
    },
    removePointDescription: function(name) {
        var pdescs = this.state['point descriptions'];
        delete pdescs[name];
        this.setState({"point descriptions": pdescs});
    },
    addPointDescription: function() {
        var pdescs = this.state['point descriptions'];
        pdescs[''] = '';
        this.setState({"point descriptions": pdescs});
    },
    render: function() {
        var pointdescriptions = _.map(this.state["point descriptions"], function(desc, name) {
            var boundClick = this.removePointDescription.bind(this, name);
            return (
                <div key={name}>
                    <Row>
                    <Col xs={4}>
                        <Input type='text' addonBefore='Name' placeholder='Point name' defaultValue={name} />
                    </Col>
                    <Col xs={7}>
                        <Input type='text' addonBefore='Description' placeholder='Point description' defaultValue={desc} />
                    </Col>
                    <Col xs={1}>
                        <Button onClick={boundClick}><Glyphicon glyph='minus'/></Button>
                    </Col>
                    </Row>
                </div>
            );
        }, this);

        var periods = _.map(this.state['periods'], function(period) {
            return (
                <SchedulePeriod {...period} />
            );
        });
        return (
            <div className="scheduleEditor">
                <Panel header="Edit Schedule" bsStyle='info'>
                    <form onSubmit={this.handleChange}>
                        <Input type='text' label='Name' value={this.state.name}/>
                        <Input rows="2" cols="50" type='textarea' label='Description' value={this.state.description} />
                        <Panel header="Point Descriptions" eventKey="1">
                            {pointdescriptions}
                            <Row>
                                <Col xs={4}>
                                    <p>Add new point description</p>
                                </Col>
                                <Col xs={8}>
                                    <Button onClick={this.addPointDescription}><Glyphicon glyph='plus'/></Button>
                                </Col>
                            </Row>
                        </Panel>

                        <br />
                        <b>Periods</b>
                        <ul>
                        <ListGroup>
                            {periods}
                        </ListGroup>
                        </ul>
                    </form>
                </Panel>
            </div>
        );
    }
});

var SchedulePeriod = React.createClass({
    render: function() {
        console.log("rendering period", this.props);
        var points = _.map(this.props.points, function(point) {
            return (
                <SchedulePoint {...point} names={_.pluck(this.props.points, 'name')}/>
            );
        }, this);
        var header = (
            <Row>
                <Col xs={2}>
                    <Input type='text' maxlength="10" size="10" addonBefore='Name' placeholder='Period name' defaultValue={this.props.name} />
                </Col>
                <Col xs={2}>
                    <Input type='text' maxlength="4" size="4" addonBefore='Start' placeholder='Period start' defaultValue={this.props.start} />
                </Col>
            </Row>
        );
        return (
            <ListGroupItem>
                <div className="schedulePeriod">
                <Panel header={header} bsStyle='warning'>
                    {points}
                </Panel>
                </div>
            </ListGroupItem>
        );
    }
});

var SchedulePoint = React.createClass({
    render: function() {
        console.log("render point", this.props);
        var options = _.map(this.props.names, function(name) {
            return (
                <option value={name} selected={name==this.props.name ? true : false}>{name}</option>
            );
        }, this);
        return (
            <div className="schedulePoint">
                <Row>
                    <Col xs={4}>
                        <Input type='select' addonBefore='Point Name'>
                            {options}
                        </Input>
                    </Col>
                    <Col xs={4}>
                        <Input type='text' addonBefore='Value' placeholder='Point value' defaultValue={this.props.value} />
                    </Col>
                    <Col xs={2}>
                        <Input type='text' defaultValue={this.props.units} />
                    </Col>
                </Row>
            </div>
        );
    }
});

