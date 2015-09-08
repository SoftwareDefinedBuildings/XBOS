var Login = React.createClass({
    doLogin: function(e) {
        //e.preventDefault();
        console.log(this.refs);
    },
    render: function() {
        return (
            <div className="login">
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
