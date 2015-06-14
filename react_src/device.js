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
                <b>Name: {this.state.name}</b>
                <p>DeviceID: {this.props.deviceID}</p>
                <p>
                    <ReactBootstrap.ModalTrigger modal={<MetadataModal deviceID={this.props.deviceID}/>}>
                        <ReactBootstrap.Button bsStyle='primary' bsSize='small'>Show Metadata</ReactBootstrap.Button>
                    </ReactBootstrap.ModalTrigger>
                </p>
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
    updateFromRepublish: function(obj) {
        var self = this;
        _.map(obj, function(data) {
            self.setState({value: get_latest_reading(data.Readings)});
        });
    },
    getInitialState: function() {
        return({value: "n/a"});
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
                <b>TIMESERIES</b>
                <p>ts uuid: {this.props.uuid} </p>
                <p>{this.props.name}: {this.state.value}</p>
                {act}
            </div>
        )
    }
});

var MetadataModal = React.createClass({
   getInitialState() {
    return {};
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
      <ReactBootstrap.Modal {...this.props} title={modaltitle} animation={false}>
        <div className='modal-body'>
            {mdrender}
        </div>
        <div className='modal-footer'>
          <ReactBootstrap.Button onClick={this.props.onRequestHide}>Close</ReactBootstrap.Button>
        </div>
      </ReactBootstrap.Modal>
    );
  } 
});
