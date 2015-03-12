/*
 * This will render a slider bar between a range with a given step interpolating between
 * the low and high ends of the range. Sliding the knob will result in a POST request being
 * performed in the backend. The required props are
 *
 * @low: number identifying the lower bound of the range
 * @high: number identifying the higher bound of the range
 * @step: the unit of interpolation between @low and @high
 * @url: the URL that will be POSTed to when the slider changes
 * @prop: the current value of the slider -- this should come from the parent element, so this is immutable
 *        for this component
 *
 * Accepted state is
 *
 * @data: a JSON object to be sent on the POST request. If empty, then this
 * will not be sent along
 */
var ContinuousActuator = React.createClass({
    render: function() {
        return(
            <div className="continuousActuator">
                <p>Slider</p>
            </div>
        );
    }
});

/*
 * This will render two buttons, one for "on" and one for "off". Clicking a button
 * will result in a POST request being performed. the required props are
 *
 * @onUrl: URL that is POSTed when the "on" button is pushed
 * @onLabel: label for the "on" button
 * @onData: data for the POST request when "on" is pushed
 *
 * @offUrl: URL that is POSTed when the "off" button is pushed
 * @offLabel: label for the "off" button
 * @offData: data for the POST request when "off" is pushed
 *
 * State:
 * @on: if @on is 1, then the "on" will be depressed (the bootstrap "active" prop), else the "off" button will be depressed
 */
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
