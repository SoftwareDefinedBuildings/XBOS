var ContinuousActuator = React.createClass({
    getInitialState: function() {
        return({loading: false});
    },
    handleSubmit: function(event) {
        event.preventDefault();
        this.setState({loading: true});
        var value = parseFloat(this.refs.value.getDOMNode().value.trim());
        if (!isNaN(value)) {
            console.log("new value", value);
            var req = {uuid: this.props.uuid, request: value};
            console.log(req);
            this.socket.emit('actuate', req);
        }
        setTimeout(function() {
            this.setState({loading: false});
            this.refs.value.getDOMNode().value = '';
        }.bind(this), 2000);
    },
    componentWillMount: function() {
        this.socket = io.connect();
    },
    render: function() {
        return(
            <div className="continuousActuator">
                <form onSubmit={this.handleSubmit} >
                  <input type="text" ref="value" />
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
        var postURL = isOnReq ? this.props.onUrl : this.props.offUrl;
        var postData = isOnReq ? this.props.onData : this.props.offData;
        $.ajax({
            url: postURL,
            dataType: 'json',
            type: 'POST',
            data: postData,
            success: function(data){
                this.setState({loading: false, on: isOnReq});
            }.bind(this),
            error: function(xhr, status, err) {
                console.log(postURL, status, err.toString());
            }.bind(this)
        });

        setTimeout(function() {
        this.setState({loading: false});
        }.bind(this), 2000);
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
