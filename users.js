var users = {};

// import config
var config = require('./config');
var mongo = require('mongoskin');
var bcrypt = require('bcrypt');

// setup MongoDB
var db = mongo.db(config.mongohost);
db.bind('users'); // bind to collection

// bcrypt.genSaltSync()
var salt = '$2a$10$2bYSu/psRge8425Vif28he';

users.findByName = function(name, cb) {
    db.users.findOne({name: name}, function(err, found) {
        if (err) {
            cb(err);
        } else if (!found) {
            cb(new Error("User with name "+name+" does not exist"));
        } else {
            cb(null, found);
        }
    })
}

users.findById = function(id, cb) {
    db.users.findOne({_id: mongo.helper.toObjectID(id)}, function(err, found) {
        if (err) {
            cb(err);
        } else if (!found) {
            cb(new Error("User with id "+id+" does not exist"));
        } else {
            cb(null, found);
        }
    })
}

users.createUser = function(name, password, cb) {
    var hash = bcrypt.hashSync(password, salt);
    var user = {name: name, password: hash};
    db.users.findOne({name: name}, function(err, found) {
        if (found) {
            cb(new Error("User already exists with name "+name));
        } else if (err) {
            cb(err);
        } else {
            db.users.insert(user, function(err) {
                if (err) {
                    cb(err);
                } else {
                    cb(null);
                }
            });
        }
    });
}

users.validPassword = function(user, password) {
    return bcrypt.compareSync(password, user.password);
}

module.exports = users;
