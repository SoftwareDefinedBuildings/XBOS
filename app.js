// dependencies
var express = require('express');
var path = require('path');
var WebSocket = require('ws');
var _ = require('underscore');
var config = require('./config');
var moment = require('moment');
var http = require('http');
var MongoClient = require('mongodb').MongoClient;
var bodyParser = require('body-parser');
var multer = require('multer');

// connect to mongodb
var sched = {};
MongoClient.connect("mongodb://"+config.mongo.host+":"+config.mongo.port+"/"+config.mongo.db, function(err, db) {
    if (!err) {
        console.log("Connected to mongodb", config.mongo);
        db.createCollection('schedules', function(err, coll) {
            console.log("'schedules' collection created");

            // import schedule from a file
            // TODO: in future, probably want to read schedule from mongodb. Importing a schedule into mongo from a file should be a tool
            sched = require(config.schedule_file);
            coll.update({name: sched.name}, sched, {upsert: true}, {w:1}, function(err, result) {
                console.log("inserted schedule");
            });
        });

    }
});


// server setup
var app = express();
app.set('views', path.join(__dirname, 'views'));
app.use(express.static('public'))
app.use(express.static('node_modules'))

// from http://expressjs.com/api.html#req.body
app.use(bodyParser.json()); // for parsing application/json
app.use(bodyParser.urlencoded({ extended: true })); // for parsing application/x-www-form-urlencoded
app.use(multer()); // for parsing multipart/form-data

app.use(function(req, res, next) {
    res.header("Access-Control-Allow-Origin", "*");
    res.header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept");
    next();
});

app.get('/', function(req, res) {
    res.render('index', {title: 'OpenBAS'});
});

// returns a list of schedule names
app.get('/schedule/list', function(req, res) {
    MongoClient.connect("mongodb://"+config.mongo.host+":"+config.mongo.port+"/"+config.mongo.db, function(err, db) {
        db.collection('schedules', function(err, coll) {
            coll.find({}, {name: 1, _id: 0}).toArray(function(err, results) {
                res.setHeader('Content-Type', 'application/json');
                res.send(JSON.stringify(results));
            });
        });
    });
});

app.get('/schedule/:name/get', function(req, res) {
    console.log("fetching schedule", req.params.name);
    MongoClient.connect("mongodb://"+config.mongo.host+":"+config.mongo.port+"/"+config.mongo.db, function(err, db) {
        db.collection('schedules', function(err, coll) {
            coll.findOne({name: req.params.name}, {_id: 0}, function(err, results) {
                res.setHeader('Content-Type', 'application/json');
                res.send(JSON.stringify(results));
            });
        });
    });
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
