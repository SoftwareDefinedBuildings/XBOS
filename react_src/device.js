var Device = React.createClass({
    getInitialState: function() {
        return({uuids: {}, name: ""});
    },

    // when we mount, fetch the UUID for each display tag we are given
    componentDidMount: function() {
        var self = this;
        var state = {uuids: {}};
        _.each(this.props.display, function(displaytag) {
            self.getUUID(displaytag);
        });
        self.setState(state);
        run_query("select Metadata/Name where "+this.props.queryBase,
                  function(data) {
                    self.setState({name: data[0]});
                  },
                  function(xhr, status, err) { // error
                    console.error("error", displaytag, LOOKUP[displaytag]);
                    console.error(queryURL, status, err.toString());
                  }
        );
    },
    // this runs a query to retrieve the UUID for a given displaytag
    getUUID: function(displaytag) {
        var self = this;
        run_query("select uuid where "+this.props.queryBase+" and "+LOOKUP[displaytag],
                  function(data) { // success
                    var uuids = self.state.uuids;
                    if (data != undefined && data.length > 0) {
                        uuids[data[0].uuid] = displaytag;
                        self.setState({"uuids": uuids});
                    }
                  },
                  function(xhr, status, err) { // error
                    console.error("error", displaytag, LOOKUP[displaytag]);
                    console.error(queryURL, status, err.toString());
                  });
    },
    render: function() {
        var timeseries = _.map(this.state.uuids, function(name, uuid) {
            var queryBase = "uuid = '"+uuid+"'";
            return (
                <Timeseries key={uuid} name={name} uuid={uuid} queryBase={queryBase}/>
            )
        });
        var cx = React.addons.classSet;
        var classes = cx({
            'devbox': true,
            'device': true
        });
        return (
            <div className={classes}>
                <Row>
                    <Col xs={6}>
                    <b>Name: {this.state.name}</b>
                    </Col>
                    <Col xs={6}>
                        <MetadataModal deviceID={this.props.deviceID} />
                    </Col>
                </Row>
                <p>DeviceID: {this.props.deviceID}</p>
                {timeseries}
            </div>
        );
    }
});


/*
 * This class wraps a UUID for a timeseries and displays both its current reading and optionally the actuator
 */
var Timeseries = React.createClass({
    mixins: [SubscribeQueryBase],
    updateFromRepublish: function(data) {
        //_.map(obj, function(data) {
        console.log("timeseries got",data)
        this.setState({value: get_latest_reading(data.Readings)});
        //});
    },
    getInitialState: function() {
        return({value: "n/a", plotlink: "#"});
    },
    componentDidMount: function() {
        var self = this;
        run_query("select * where uuid = '"+this.props.uuid+"'",
                  function(data) { // success
                    self.setState(data[0])
                  },
                  function(xhr, status, err) { // error
                    console.error("error", displaytag, LOOKUP[displaytag]);
                    console.error(queryURL, status, err.toString());
                  });
        get_permalink([this.props.uuid], 
        function(url) {
            self.setState({plotlink: url});
        },
        function(xhr) {
            console.error(xhr);
        }
        );
    },
    render: function() {
        var act = (<span />);
        if (this.state.Actuator != undefined) {
            act = (<Actuator ActuatorUUID={this.state.Actuator.uuid}/>);
        }
        var cx = React.addons.classSet;
        var classes = cx({
            'tsbox': true,
            'timeseries': true
        });
        return (
            <div className={classes}>
                <Row>
                    <Col xs={4}>
                    <p>{this.props.name}: <b>{isNumber(this.state.value) ? this.state.value.toFixed(2) : this.state.value }</b></p>
                    </Col>
                    <Col xs={8}>
                        <p>{this.props.uuid} </p>
                    </Col>
                </Row>
                <Row>
                    <Col xs={2}>
                    <Button href={this.state.plotlink} bsStyle="info">Plot</Button>
                    </Col>
                    <Col xs={6}>
                    {act}
                    </Col>
                    <Col xs={4}></Col>
                </Row>
            </div>
        )
    }
});

var MetadataModal = React.createClass({
   getInitialState() {
    return {show: false};
   },
   open() {
    this.setState({show: true});
   },
   close() {
    this.setState({show: false});
   },
   componentWillMount(data) {
    var self = this;
    run_query("select * where Metadata/DeviceID = '"+this.props.deviceID+"'",
             function(data) {
                self.setState(get_device_view(data)._Metadata);
             },
             function(xhr, status, err) { // error
               console.error("error", displaytag, LOOKUP[displaytag]);
               console.error(queryURL, status, err.toString());
             });
   },
   render() {
    var mdrender = _.map(this.state, function(value, key) {
        return (<p key={key}><b>{key}</b>: {value}</p>)
    });
    var modaltitle = 'Metadata for DeviceID ' + this.props.deviceID;
    return (
      <div className="metadataModal">
        <Button bsStyle='primary' bsSize='small' onClick={this.open}>Show Metadata</Button>
        <Modal {...this.props} show={this.state.show} onHide={this.close} animation={false}>
          <Modal.Header closeButton>
              <Modal.Title>{modaltitle}</Modal.Title>
          </Modal.Header>
          <Modal.Body>
              {mdrender}
          </Modal.Body>
          <Modal.Footer>
            <Button onClick={this.close}>Close</Button>
          </Modal.Footer>
        </Modal>
      </div>
    );
  } 
});
