// local imports
var config = require('./config');
var schedule = require('./schedule');

// dependencies
var express = require('express');
var request = require('request');
var path = require('path');
var WebSocket = require('ws');
var _ = require('underscore');
var moment = require('moment');
var exphbs  = require('express-handlebars');
var http = require('http');
var MongoClient = require('mongodb').MongoClient;
var bodyParser = require('body-parser');
var multer = require('multer');
var passport = require('passport');
var LocalStrategy = require('passport-local').Strategy;
var users = require('./users');

passport.use(new LocalStrategy(
      function(username, password, done) {
        users.findByName(username, function(err, user) {
          if (err) { return done(err); }
          if (!user) { return done(null, false, { message: 'Incorrect username.' }); }
          if (!users.validPassword(user, password)) { return done(null, false, { message: 'Incorrect password.' }); }
          return done(null, user);
        });
      }
));

passport.serializeUser(function(user, cb) {
  cb(null, user._id);
});

passport.deserializeUser(function(_id, cb) {
  users.findById(_id, function (err, user) {
    if (err) { return cb(err); }
    cb(null, user);
  });
});

// server setup
var app = express();
app.engine('handlebars', exphbs({defaultLayout: 'main'}));
app.set('view engine', 'handlebars');
app.use(express.static('public'))
app.use(express.static('node_modules'))
app.use(bodyParser.json() );       // to support JSON-encoded bodies
app.use(bodyParser.urlencoded({     // to support URL-encoded bodies
  extended: true
}));
app.use(require('cookie-parser')());
app.use(require('express-session')({ secret: config.session_secret, resave: false, saveUninitialized: false }));
app.use(passport.initialize());
app.use(passport.session());

app.use(function(req, res, next) {
    res.header("Access-Control-Allow-Origin", "*");
    res.header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept");
    next();
});

app.get('/', function(req, res) {
    if (req.isAuthenticated()) {
        res.render('index', {layout: false});
    } else {
        res.redirect('/login');
    }
});

app.get('/dashboard', function(req, res) {
    if (req.isAuthenticated()) {
        res.render('index', {layout: false});
    } else {
        res.redirect('/login');
    }
});

app.get('/deckard', function(req, res) {
    res.redirect(config.deckard);
});

app.get('/plotter', function(req, res) {
    res.redirect(config.plotter);
});

app.post('/permalink', function(req, res) {
    if (!req.isAuthenticated()) {
        res.redirect('/login');
        return;
    }
    var streams = _.map(req.body.uuid, function(uuid) {
        return {"stream": uuid}
    });
    var spec = {
        "window_type": "now",
        "window_width": 8.64e13, // 1 day
        "streams": streams
    }
    var tosend = {"permalink_data": JSON.stringify(spec)};
    request.post({url: config.plotter+"/s3ui_permalink", json: tosend}, function(err, remoteResponse, remoteBody) {
        if (err) { return res.status(500).end(err.message, remoteBody, remoteResponse); }
        res.end(config.plotter+"/?"+remoteBody);
    });
});

app.get('/schedule', function(req, res) {
    if (!req.isAuthenticated()) {
        res.redirect('/login');
        return;
    }
    res.render('schedule', {layout: false});
});

app.get('/schedule_edit', function(req, res) {
    if (!req.isAuthenticated()) {
        res.redirect('/login');
        return;
    }
    if (!req.user.admin) {
        res.redirect('/schedule');
        return;
    }
    res.render('schedule_edit', {layout: false});
});

app.get('/schedule/list', function(req, res) {
    if (!req.isAuthenticated()) {
        res.redirect('/login');
        return;
    }
    schedule.list(
        function(result) {
            res.json(result);
        },
        function(err) {
            res.status(500).end(err.message);
        }
    )
});

app.get('/schedule/name/:name', function(req, res) {
    if (!req.isAuthenticated()) {
        res.redirect('/login');
        return;
    }
    schedule.get(req.params.name,
        function(result) {
            res.json(result);
        },
        function(err) {
            res.status(500).end(err.message);
        }
    )
});

app.post('/schedule/save', function(req, res) {
    if (!req.isAuthenticated()) {
        res.redirect('/login');
        return;
    }
    if (!req.user.admin) {
        res.end();
        return;
    }
    var sched = req.body;
    console.log(sched);
    schedule.save(sched,
        function() {
            res.end();
        },
        function(err) {
            res.status(500).end(err.message);
        }
    )
});

app.post('/schedule/delete', function(req, res) {
    if (!req.isAuthenticated()) {
        res.redirect('/login');
        return;
    }
    if (!req.user.admin) {
        res.redirect('/schedule');
        return;
    }
    schedule.delete(req.body.name,
        function() {
            res.end();
        },
        function(err) {
            res.status(500).end(err.message);
        }
    )
});

app.post('/query', function(req, res) {
    var mypost = {
        url: config.httpArchiverUrl+'/api/query',
        body: req.body.query,
        method: 'POST'
    };
    request(mypost, function(err, resp, body) {
        if (!err&& resp.statusCode == 200) {
            res.json(JSON.parse(body));
        } else {
            res.status(500).end(resp.body);
        }
    });
});


// login stuff
app.get('/login', function(req, res) {
    res.render('login', {layout: false});
});

app.get('/logout', function(req, res) {
    req.logout();
    res.redirect('/login');
});

app.post('/login', 
    passport.authenticate('local', { failureRedirect: '/login' }),
    function(req, res) {
        res.redirect('/');
});

var server = app.listen(config.port, config.host);
console.log('Server listening on port '+config.port);

// keep track of mapping from subscriptions to the queries for those subscriptions
var wsconns = {};

// socket.io setup
var io = require('socket.io')(server);

// socket.io triggers (server <-> clients/reactjs)
io.on('connection', function (socket) {
    console.log('New client connected!');

    // listen for a new subscription
    socket.on('new subscribe', function(msg) {

        // check if we already have a websocket for that connection.
        // If we already do, ignore.
        if (!_.has(wsconns, msg)) {
            console.log('new subscribe req', msg);

            // create a websocket for that subscription
            wsconns[msg] = new WebSocket(config.wsArchiverUrl+'/republish');

            // on opening the websocket, send the query message
            wsconns[msg].on('open', function open() {
                wsconns[msg].send(msg);
                console.log('opened', msg);
            });

            // when we receive a message from the server, emit the result
            // back to each of the clients
            wsconns[msg].on('message', function(data, flags) {
                io.emit(msg, JSON.parse(data));
            });

            wsconns[msg].on('close', function() {
                console.log('disconnected!');
            });
        }
    });

    var smapActuateMsg = {
        '/actuate': {
            Metadata: {override: ''},
            Readings: [],
            uuid: config.uuid,
        },
    };
    var smapPost = {
        hostname: config.httpArchiverHost,
        port: config.httpArchiverPort,
        path: '/add/'+config.apikey,
        method: 'POST'
    };
    socket.on('actuate', function(msg) {

        smapActuateMsg['/actuate'].Metadata.override = msg.uuid
        smapActuateMsg['/actuate'].Readings[0] = [moment().valueOf(), msg.request];
        console.log("Actuation requested for", smapActuateMsg);
        var req = http.request(smapPost, function(res) {
            console.log('STATUS',res.statusCode);
            res.on('data', function(chunk) {
                console.log('BODY',chunk);
            });
        });
        req.on('error', function(e) {
            console.error("Problem POSTing to archiver:", e.message);
        });
        req.write(JSON.stringify(smapActuateMsg));
        req.end();
    });
});
