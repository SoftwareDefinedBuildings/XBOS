var Login = React.createClass({
    doLogin: function(e) {
        //e.preventDefault();
        console.log(this.refs);
    },
    render: function() {
        var styles = {};
        styles["margin"] = "0 auto";
        styles["width"] = "400px";
        return (
            <div style={{margin: "0 auto", width: "400px"}} className="login">
                <form action="/login" method="post">
                    <Input name="username" type='text' ref='user' label='User' />
                    <Input name="password" type='password' ref='pass' label='Password' />
                    <Button type='submit' bsStyle='success'>Submit</Button>
                </form>
            </div>
        )
    }
});

React.render(
    <Login />,
    document.getElementById('content')
);
