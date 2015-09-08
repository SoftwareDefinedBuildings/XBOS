var config = {};

config.port = 7000;
config.host = '0.0.0.0';

config.session_secret = 'replace me';
// bcrypt.genSaltSync()
config.salt = '$2a$10$2bYSu/psRge8425Vif28he';

config.apikey = "ADM5fw0z1HdbMCDZ6JSQAveuZyKDc_GicOsKBqzznpySgiUrmLENUGcqF69PXhXFgXOQ_GS98TUt0O-8SHXgKg==";
config.uuid = "15fbd44c-c3c4-11e4-95aa-0cc47a0f7eea";
config.httpArchiverHost = 'localhost';
config.httpArchiverPort = 8079;
config.httpArchiverUrl = 'http://'+config.httpArchiverHost+":"+config.httpArchiverPort;
config.wsArchiverHost = 'localhost';
config.wsArchiverPort = 8078;
config.wsArchiverUrl = 'ws://'+config.wsArchiverHost+":"+config.wsArchiverPort;

// configuration for connection to MongoDB
config.mongohost = 'mongodb://localhost:27017/xbos';

module.exports = config;

