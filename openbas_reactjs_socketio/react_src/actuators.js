var ContinuousActuator = React.createClass({
    getInitialState: function() {
        return({loading: false,
                value: this.props.initialValue});
    },
    handleSubmit: function(event) {
        event.preventDefault();
        var value = parseFloat(this.refs.value.getDOMNode().value.trim());
        this.setState({loading: true});
        console.log("new value", value);
        if (!isNaN(value)) {
            var req = {uuid: this.props.uuid, request: value};
            console.log(req);
            this.socket.emit('actuate', req);
        }
        setTimeout(function() {
            this.setState({loading: false, value: value});
            this.refs.value.getDOMNode().value = '';
        }.bind(this), 2000);
    },
    componentWillMount: function() {
        this.socket = io.connect();
    },
    componentDidMount: function() {
        console.log("continuous actuator", this.props);
    },
    render: function() {
        return(
            <div className="continuousActuator">
                <form onSubmit={this.handleSubmit} >
                  <input type="text" ref="value" maxLength="4" size="4" />
                  { !this.state.loading ?  <input type="submit" value="Override" /> : <label>Loading...</label> }
                </form>
            </div>
        );
    }
});


var BinaryActuator = React.createClass({
    getInitialState: function() {
        return({on: false,
                loading: false});
    },
    handleClick: function(e) {
        this.setState({loading: true});
        var isOnReq = e.target.getAttribute('data-buttontype') == 'on';

        var req = {uuid: this.props.uuid, request: isOnReq ? 1 : 0};
        this.socket.emit('actuate', req);

        setTimeout(function() {
        this.setState({loading: false});
        }.bind(this), 2000);
    },
    componentWillMount: function() {
        this.socket = io.connect();
    },
    componentDidMount: function() {
        console.log('props',this.props);
    },
    render: function() {
        var Button = ReactBootstrap.Button;
        var ButtonToolbar = ReactBootstrap.ButtonToolbar;
        var onActive = this.state.on;
        var offActive = !this.state.on;
        return(
            <div className="binaryActuator">
                <ButtonToolbar>
                    <Button bsStyle="success" 
                            disabled={this.state.loading} 
                            active={onActive} 
                            data-buttontype="on"
                            onClick={!this.state.loading ? this.handleClick : null}>
                    {this.state.loading ? 'Loading...' : this.props.onLabel}
                    </Button>

                    <Button bsStyle="danger" 
                            disabled={this.state.loading} 
                            active={offActive} 
                            data-buttontype="off"
                            onClick={!this.state.loading ? this.handleClick : null}>
                    {this.state.loading ? 'Loading...' : this.props.offLabel}
                    </Button>
                </ButtonToolbar>
            </div>
        );
    }
});
