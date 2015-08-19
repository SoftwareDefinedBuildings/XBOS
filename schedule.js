var schedule = {};

// import config
var config = require('./config');
var mongo = require('mongoskin');

// setup MongoDB
var db = mongo.db(config.mongohost);
db.bind('schedules'); // bind to collection

schedule.list = function(success, error) {
    db.schedules.distinct("name", {}, function(err, found) {
        if (err || !found) {
            error(err);
        } else {
            success(found);
        }
    });
}

schedule.get = function(name, success, error) {
    db.schedules.findOne({name: name}, function(err, found) {
        if (err || !found) {
            error(err);
        } else {
            delete found._id;
            success(found);
        }
    });
}

module.exports = schedule;
