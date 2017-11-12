/**
 * Created by admin on 2016/8/16.
 */

var app = require('express')();
var http = require('http').Server(app);
var io = require('socket.io')(http);
var redis = require('redis');
var mysql = require('mysql');
const crypto = require('crypto');
const assert = require('assert');
var log4js = require('log4js');

var logger = log4js.getLogger();
logger.level = 'debug';
// logger.setLevel(log4js.levels.DEBUG);

const CLASS_C = 'C';
const CLASS_B = 'B';
const CLASS_A = 'A';
const QUE_DOWN = 'QUE_DOWN:';
const CHANNEL_QUE_DOWN_C = 'que_down_alarm_c:';
const CHANNEL_QUE_DOWN_B = 'que_down_alarm_b:';
const CHANNEL_QUE_DOWN_MULTI = 'que_down_alarm_multi:';
const CHANNEL_MSG_UP = 'msg_alarm:';
const CHANNEL_JOIN_REQ = 'join_request:';
const CHANNEL_JOIN_SUCCESS = 'join_success:';
const CHANNEL_JOIN_ACCEPT = 'join_accept:';
const CHANNEL_JOIN_ERROR = 'join_error:';
const DEV = 'DEV:';
const GROUP = 'GROUP:';
const MSG_UP = 'UP_M:';

var redis_db = redis.createClient({
    'password': 'niotloraredis',
    'db': 10,
    'return_buffers': true
});
// var redis_db = require('redis-connection-pool')('myRedisPool', {
//     host: '127.0.0.1', // default 
//     port: 6379, //default 
//     // optionally specify full redis url, overrides host + port properties 
//     // url: "redis://username:password@host:port" 
//     max_clients: 30, // defalut 
//     perform_checks: false, // checks for needed push/pop functionality 
//     database: 10, // database number to use 
//     options: {
//         auth_pass: 'niotloraredis'
//     } //options for createClient of node-redis, optional 
// });

// var sql_conn = mysql.createConnection({
var sql_conn = mysql.createPool({
    host: 'localhost',
    port: 3306,
    socketPath: '/opt/data/mysql/mysql.sock',
    user: 'pro_nwkserver',
    password: 'niotlorasql',
    database: 'nwkserver'
});

// sql_conn.connect();

io.on('connection', function(client) {
    var app_eui = client.handshake.query.app_eui;
    var token = client.handshake.query.token;
    logger.debug('connecting: ', app_eui, token);
    var app_eui_buffer = eui_validator(app_eui);
    if (app_eui_buffer == null) {
        client.error('app_eui is required in query, expect a 16 hex string');
        client.disconnect();
        return
    }
    app_eui = app_eui.toLowerCase();
    sql_conn.query('SELECT token FROM app WHERE hex(app_eui)="' + app_eui + '"', function(err, rows, fields) {
        if (rows[0]) {
            var token_auth = rows[0].token;
            token_auth = cipher_token(app_eui_buffer.slice(0, 8), token_auth);
            if (token_auth == token) {
                listen(client, app_eui_buffer);
                sql_conn.query('SELECT dev_eui FROM device WHERE hex(app_eui)="' + app_eui + '"', function(err, rows, fields) {
                    for (var i = 0; i < rows.length; i++) {
                        rows[i].dev_eui = rows[i].dev_eui.toString('hex');
                    }
                    client.emit('devices', rows);
                });
                redis_db.smembers('GROUPS_APP:' + app_eui, function(err, reply) {
                    for (var i = 0; i < reply.length; i++) {
                        reply[i] = {
                            id: reply[i].toString('hex')
                        };
                    }
                    client.emit('groups', reply);
                });
            } else {
                client.error('Incorrect token');
                client.disconnect();
            }
        } else {
            client.error('App ' + app_eui + ' doesn\'t exist');
            client.disconnect();
        }
    });
});

// key and token are Buffer
function cipher_token(key, token) {
    var plaintext = token.toString('binary');
    var iv = new Buffer(0);
    var cipher = crypto.createCipheriv("des-ecb", key, iv);
    cipher.setAutoPadding(false);
    var c = cipher.update(plaintext, 'binary', 'hex');
    c += cipher.final('hex');
    var final = new Buffer(c, 'hex');
    return final.toString('base64').replace(/\+/g, '-') // Convert '+' to '-'
        .replace(/\//g, '_') // Convert '/' to '_'
        .replace(/=+$/, ''); // Remove ending '='
}

function listen(client, app_eui) {
    var sub = redis.createClient({
        'password': 'niotloraredis',
        'db': 10
    });

    var hex_app_eui = app_eui.toString('hex');

    sub.on('message', function(channel, message) {
        redis_db.hgetall(message, function(err, obj) {
            if (channel == CHANNEL_MSG_UP + hex_app_eui) {
                var name_array = message.split(':');
                if (name_array[0] == 'MSG_UP') {
                    makeMsg(obj, parseFloat(name_array[3]), name_array[2]);
                    client.emit('post_rx', obj);
                } else if (name_array[0] == 'MSG_DOWN') {
                    makeMsg(obj, parseFloat(name_array[3]), name_array[2]);
                    if (name_array[1] == 'DEV') {
                        obj.type = 'unicast';
                    } else {
                        obj.type = 'multicast';
                    }
                    client.emit('confirm_tx', obj);
                }
            } else if (channel == CHANNEL_JOIN_REQ + hex_app_eui) {
                message = JSON.parse(message);
                var obj = {
                    freq: message.trans_params.freq,
                    datr: message.trans_params.datr,
                    ts: message.ts,
                    rssi: message.trans_params.rssi,
                    lsnr: message.trans_params.lsnr,
                    data: message.request_msg,
                    eui: message.dev_eui,
                    type: 'join-req'
                };
                client.emit('otaa', obj);
            } else if (channel == CHANNEL_JOIN_SUCCESS + hex_app_eui) {
                message = JSON.parse(message);
                message.eui = message.dev_eui;
                delete message.dev_eui;
                message.type = 'join-success';
                client.emit('otaa', message);
            } else if (channel == CHANNEL_JOIN_ACCEPT + hex_app_eui) {
                message = JSON.parse(message);
                message.eui = message.dev_eui;
                message.freq = message.trans_params.freq;
                message.datr = message.trans_params.datr;
                message.type = 'join-accept';
                delete message.dev_eui;
                delete message.trans_params;
                client.emit('otaa', message);
            } else if (channel == CHANNEL_JOIN_ERROR + hex_app_eui) {
                message = JSON.parse(message);
                message.eui = message.dev_eui;
                delete message.dev_eui;
                message.type = 'join-error';
                client.emit('otaa', message);
            }
        });
    });

    sub.subscribe(CHANNEL_MSG_UP + hex_app_eui);
    sub.subscribe(CHANNEL_JOIN_REQ + hex_app_eui);
    sub.subscribe(CHANNEL_JOIN_SUCCESS + hex_app_eui);
    sub.subscribe(CHANNEL_JOIN_ERROR + hex_app_eui);
    sub.subscribe(CHANNEL_JOIN_ACCEPT + hex_app_eui);

    client.on('error', function(err) {
        logger.debug('error', err);
    });

    client.on('cache_query', function(data) {
        logger.debug(data)
        if (data && data.filter) {
            var filter = data.filter;
        }
        var token = data.token;
        var from = 0;
        var to = -1;
        var max = -1;
        var eui = null;
        if (filter) {
            if (filter.from) from = parseInt(filter.from);
            if (filter.to) to = parseInt(filter.to);
            if (filter.max) max = parseInt(filter.max);
            if (filter.eui) eui = filter.eui;
        }
        if (data && data.per_page) {
            var per_page = data.per_page;
        } else {
            var per_page = 100;
        }
        if (eui) {
            var pattern = MSG_UP + hex_app_eui + ':' + eui.toLowerCase() + '*';
        } else {
            var pattern = MSG_UP + hex_app_eui + ':' + '*';
        }
        redis_db.keys(pattern, function(err, res) {
            var tmp_arr = [];
            for (var i = 0; i < res.length; i++) {
                var name = res[i];
                name = name.toString();
                var name_array = name.split(':');
                var ts = parseInt(name_array[3]);
                var eui = name_array[2];
                if (ts > from && ((to < 0) || (ts < to))) {
                    tmp_arr.push([ts, name, eui])
                }
            }
            // sort as asc
            tmp_arr.sort(function(a, b) {
                return a[0] - b[0]
            });
            if ((max > 0) && tmp_arr.length > max) {
                tmp_arr.splice(0, tmp_arr.length - max);
            }
            var total_msg = tmp_arr.length;
            var total_page = tmp_arr.length / per_page;
            if (total_page > parseInt(total_page)) {
                total_page = parseInt(total_page) + 1;
            }
            for (var i = 0; i < total_page; i++) {
                sendCacheQuery(i, per_page, total_page, tmp_arr.splice(0, per_page), filter, token);
            }
        });
    });
    var sendCacheQuery = function(page, per_page, total_page, arr, filter, token) {
        var cache = [];
        var total_msg = arr.length;
        for (var j = 0; j < per_page; j++) {
            var name = arr.shift();
            if (name) {
                getInfo(name, function(name, err, obj) {
                    makeMsg(obj, name[0], name[2]);
                    cache.push(obj);
                    if (cache.length == total_msg || cache.length == per_page) {
                        var message = {
                            'filter': filter,
                            'page': page,
                            'per_page': per_page,
                            'total': total_page,
                            'cache': cache
                        };
                        if (token) message.token = token;
                        client.emit('cache_query', message);
                    }
                })
            } else {
                break;
            }
        }
    }

    var getInfo = function(key, callback) {
        redis_db.hgetall(key[1], function(err, obj) {
            callback(key, err, obj);

        });
    };


    client.on('tx', function(data) {
        logger.debug(data)
        var errors = {};
        var eui_buffer = eui_validator(data.eui);
        if (eui_buffer == null) {
            errors.eui = 'eui(device eui or group id) is required, expect a 16 hex string.';
            emit_ack_tx_error(client, errors, data.type, data.eui, data.nonce);
        } else {
            data.eui = data.eui.toLowerCase();
            if (data.type == 'unicast') {
                redis_db.hget(DEV + data.eui, 'app_eui', function(err, reply) {
                    if (reply == null) {
                        errors.eui = 'Data enqueue failed. Device ' + data.eui + ' is not exist or is not active.';
                        emit_ack_tx_error(client, errors, data.type, data.eui, data.nonce);
                    } else if (!reply.equals(app_eui)) {
                        errors.eui = 'Data enqueue failed. Device ' + data.eui + ' is not registered in this app';
                        emit_ack_tx_error(client, errors, data.type, data.eui, data.nonce);
                    } else {
                        var que_down = new QueDownDev(data.eui, app_eui);
                        que_down.push_msg(data.port, data.data, data.cipher, data.seqno, data.confirmed, data.rx_window, function(result) {
                            if (result[0] == true) {
                                var ack_msg = {
                                    'success': true,
                                    'type': data.type,
                                    'eui': data.eui,
                                    'data': data.data
                                };
                                if (data.nonce) ack_msg.nonce = data.nonce;
                                client.emit('ack_tx', ack_msg);
                            } else {
                                Object.assign(errors, result[1]);
                                emit_ack_tx_error(client, errors, data.type, data.eui, data.nonce);
                            }
                        });

                    }
                });
            } else if (data.type == 'multicast') {
                redis_db.hget(GROUP + data.eui, 'app_eui', function(err, reply) {
                    if (reply == null) {
                        errors.eui = 'Data enqueue failed. GROUP ' + data.eui + ' is not exist.';
                        emit_ack_tx_error(client, errors, data.type, data.eui, data.nonce);
                    } else if (!reply.equals(app_eui)) {
                        errors.eui = 'Data enqueue failed. GROUP ' + data.eui + ' is not registered in this app';
                        emit_ack_tx_error(client, errors, data.type, data.eui, data.nonce);
                    } else {
                        var que_down = new QueDownGroup(data.eui, app_eui);
                        que_down.push_msg(data.port, data.data, data.cipher, data.seqno, function(result) {
                            if (result[0] == true) {
                                var ack_msg = {
                                    'success': true,
                                    'type': data.type,
                                    'eui': data.eui,
                                    'data': data.data
                                };
                                if (data.nonce) ack_msg.nonce = data.nonce;
                                client.emit('ack_tx', ack_msg);
                            } else {
                                Object.assign(errors, result[1]);
                                emit_ack_tx_error(client, errors, data.type, data.eui, data.nonce);
                            }
                        });

                    }
                });
            } else {
                errors.type = 'type is required, expect "unicast" or "multicast".';
            }
        }
    });

    client.on('disconnect', function() {
        logger.debug('disconnect', client.id, app_eui);
        sub.unsubscribe();
    });

}

function emit_ack_tx_error(client, errors, type, eui, nonce) {
    var ack_msg = {
        'success': false,
        'type': type,
        'eui': eui,
        'errors': errors
    };
    if (nonce) ack_msg.nonce = nonce;
    client.emit('ack_tx', ack_msg);
}


function eui_validator(eui) {
    if (eui) {
        try {
            if (eui.length != 16) throw new TypeError();
            return new Buffer(eui, "hex");
        } catch (TypeError) {
            return null
        }
    }
}

var num_properties = ['lsnr', 'freq', 'fcnt', 'rssi'];
var hex_properties = ['data', 'nonce'];
var bool_properties = ['cipher'];

function makeMsg(obj, ts, eui) {
    parseMsg(obj);
    obj.ts = ts;
    obj.eui = eui;
}

function parseMsg(obj) {
    for (var key in obj) {
        if (hex_properties.indexOf(key) > -1) {
            obj[key] = obj[key].toString('hex')
        } else if (bool_properties.indexOf(key) > -1) {
            obj[key] = Boolean(parseInt(obj[key].toString()));
        } else if (num_properties.indexOf(key) > -1) {
            obj[key] = parseFloat(obj[key].toString());
        } else {
            obj[key] = obj[key].toString();
        }
    }
}


class QueDownDev {
    constructor(hex_eui, app_eui) {
        var key = DEV + hex_eui;
        this.app_eui = app_eui;
        this.key = key;
    }
    push_msg(port, payload, cipher = true, seqno = null, confirmed = false, rx_window = 0, callback) {
        var key = this.key;
        if (!(port === parseInt(port, 10)) && (port > 0) && (port < 256))
            return callback([false, {
                'port': 'Invalid port, expect Integer from 1 - 255'
            }]);
        try {
            payload = new Buffer(payload, 'hex');
        } catch (TypeError) {
            return callback([false, {
                'data': 'Invalid data, expect hex string'
            }]);
        }
        if (typeof cipher != 'boolean') {
            return callback([false, {
                'cipher': 'Invalid cipher, expect boolean value'
            }]);
        }
        if (cipher == false) {
            redis_db.hget(key, 'appskey', function(err, reply) {
                if (reply.length != 16)
                    return callback([false, {
                        'cipher': 'cipher cannot be false because appskey is absent'
                    }]);
                payload = que_down_dev_gen_msg(cipher, rx_window, confirmed, port, payload);
                que_down_dev_save(key, payload, rx_window, callback);

            });
        } else {
            if (seqno == null || !(seqno === parseInt(seqno, 10)))
                return callback([false, {
                    'seqno': 'if cipher is true, seqno is required and is a integer represent fcnt of this downlink'
                }]);
            redis_db.hget(key, 'fcnt_down', function(err, reply) {
                var fcnt_down = parseInt(reply.toString());
                redis_db.llen(QUE_DOWN + this.key, function(err, reply) {
                    var que_len = parseInt(reply.toString());
                    var seqno_expect = fcnt_down + que_len + 1;
                    if (seqno != seqno_expect) {
                        return callback([false, {
                            'seqno': 'seqno doesn\'t match, expect seqno ' + seqno_expect
                        }]);
                    }
                    payload = que_down_dev_gen_msg(cipher, rx_window, confirmed, port, payload);
                    que_down_dev_save(key, payload, rx_window, callback);
                });
            });
        }
    }
}

function que_down_dev_save(key, payload, rx_window, callback) {
    redis_db.hget(key, 'dev_class', function(err, reply) {
        var dev_class = reply.toString();
        if (dev_class == CLASS_C && rx_window == 1) redis_db.rpush(QUE_DOWN + key + ':1', payload);
        else redis_db.rpush(QUE_DOWN + key, payload);
        if (dev_class == CLASS_C && rx_window != 1)
            redis_db.publish(CHANNEL_QUE_DOWN_C, key);
        else if (dev_class == CLASS_B)
            redis_db.publish(CHANNEL_QUE_DOWN_B, key);
        return callback([true, '']);
    });
}

class QueDownGroup {
    constructor(hex_eui, app_eui) {
        var key = GROUP + hex_eui;
        this.app_eui = app_eui;
        this.key = key;
    }
    push_msg(port, payload, cipher = true, seqno = null, callback) {
        var key = this.key;
        if (!(port === parseInt(port, 10)) && (port > 0) && (port < 256))
            return callback([false, {
                'port': 'Invalid port, expect Integer from 1 - 255'
            }]);
        try {
            payload = new Buffer(payload, 'hex');
        } catch (TypeError) {
            return callback([false, {
                'data': 'Invalid data, expect hex string'
            }]);
        }
        if (typeof cipher != 'boolean') {
            return callback([false, {
                'cipher': 'Invalid cipher, expect boolean value'
            }]);
        }
        if (cipher == false) {
            redis_db.hget(key, 'appskey', function(err, reply) {
                if (reply.length != 16)
                    return callback([false, {
                        'cipher': 'cipher cannot be false because appskey is absent'
                    }]);
                payload = que_down_group_gen_msg(cipher, port, payload);
                que_down_group_save(key, payload, callback);
            });
        } else {
            if (seqno == null || !(seqno === parseInt(seqno, 10)))
                return callback([false, {
                    'seqno': 'if cipher is true, seqno is required and is a integer represent fcnt of this downlink'
                }]);
            redis_db.hget(key, 'fcnt_down', function(err, reply) {
                var fcnt_down = parseInt(reply.toString());
                redis_db.llen(QUE_DOWN + this.key, function(err, reply) {
                    var que_len = parseInt(reply.toString());
                    var seqno_expect = fcnt_down + que_len + 1;
                    if (seqno != seqno_expect) {
                        return callback([false, {
                            'seqno': 'seqno doesn\'t match, expect seqno ' + seqno_expect
                        }]);
                    }
                    payload = que_down_group_gen_msg(cipher, rx_window, confirmed, port, payload);
                    que_down_group_save(key, payload, callback);
                });
            });
        }
    }
}


function que_down_group_save(key, payload, callback) {
    redis_db.rpush(QUE_DOWN + key, payload);
    redis_db.publish(CHANNEL_QUE_DOWN_MULTI, key);
    return callback([true, '']);
}

function que_down_dev_gen_msg(cipher, rx_window, confirmed, port, payload) {
    confirmed = confirmed ? 1 : 0;
    cipher = cipher ? 1 : 0;
    var settings = new Buffer([(cipher << 7) + (rx_window << 5) + (confirmed << 4)]);
    port = new Buffer([port]);
    return Buffer.concat([settings, port, payload]);
}

function que_down_group_gen_msg(cipher, port, payload) {
    cipher = new Buffer([cipher]);
    port = new Buffer([port]);
    return Buffer.concat([cipher, port, payload]);
}


http.listen(8300, function() {
    logger.debug('listening on *:8300')
});