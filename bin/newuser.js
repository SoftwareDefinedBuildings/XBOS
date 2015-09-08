#!/usr/bin/env node
var users = require('../users');

var args = process.argv;
var name = args[2];
var password = args[3];
var isadmin = (args[4] === 'true');

if (name == null || password == null) {
    console.error("Need to provide user and password");
    process.exit(1);
}

users.createUser(name, password, isadmin, function(err, ok) {
    if (err) {
        console.error(err);
        process.exit(1);
    }
    console.log("Created user with name "+name);
    console.log("is admin?", isadmin);
    process.exit(0);
});
