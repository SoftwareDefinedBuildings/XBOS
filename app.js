// local imports
var config = require('./config');
var schedule = require('./schedule');

// dependencies
var express = require('express');
var path = require('path');
var WebSocket = require('ws');
var _ = require('underscore');
var moment = require('moment');
var exphbs  = require('express-handlebars');
var http = require('http');
var MongoClient = require('mongodb').MongoClient;
var bodyParser = require('body-parser');
var multer = require('multer');

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

app.use(function(req, res, next) {
    res.header("Access-Control-Allow-Origin", "*");
    res.header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept");
    next();
});

app.get('/', function(req, res) {
    res.render('index', {layout: false});
});

app.get('/dashboard', function(req, res) {
    res.render('index', {layout: false});
});

app.get('/schedule', function(req, res) {
    res.render('schedule', {layout: false});
});

app.get('/schedule/list', function(req, res) {
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
    console.log(req.params.name);
    schedule.get(req.params.name,
        function(result) {
            res.json(result);
        },
        function(err) {
            res.status(500).end(err.message);
        }
    )
});

var server = app.listen(8000);
console.log('Server listening on port 8000');

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
