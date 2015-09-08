#!/usr/bin/env node
var bcrypt = require('bcrypt');
console.log(bcrypt.genSaltSync());
