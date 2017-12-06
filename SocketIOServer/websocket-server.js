var log4js = require('log4js');
var logger = log4js.getLogger();
logger.level = 'debug';
const WebSocket = require('ws');

const io = require('socket.io-client');
var devDataCache = {};

var socket = io('http://localhost:8300?app_eui=0000000000000001&token=fK4cRvJni0z1Gvgx3XyE0w', {
	reconnection: true
});
socket.on('post_rx', function(data) {
	if (data.eui in devDataCache) {
		devDataCache[data.eui]['lastData'] = hexToAscii(data.data)
		if ("webSocket" in devDataCache[data.eui]) {
			logger.debug('webSocket exist , need send to webSocket')
			devDataCache[data.eui].webSocket.send(JSON.stringify({
				dev: data.eui,
				timestamp: parseInt(new Date().getTime() / 1000),
				dataFrame: devDataCache[data.eui].lastData,
				status: ''
			}))
			if (devDataCache[data.eui].lastAct == 'close' && devDataCache[data.eui].lastData.indexOf("SW:0") > 0) {
				delete devDataCache[data.eui].webSocket
			} else if (devDataCache[data.eui].lastAct == 'open' && devDataCache[data.eui].lastData.indexOf("SW:1") > 0) {
				delete devDataCache[data.eui].webSocket
			}
		}
	} else {
		devDataCache[data.eui] = {
			lastData: hexToAscii(data.data)
		};
	}
});
socket.on('connect', function(data) {
	var ctimeSecond = parseInt(new Date().getTime() / 1000)
	socket.emit('cache_query', {
		filter: {
			from: ctimeSecond
		},
		token: 0
	});
	logger.debug('connect', socket.id);
});
socket.on('disconnect', function(data) {
	logger.debug('disconect', data);
});
socket.on('reconnecting', function(data) {
	logger.debug('reconecting', data, socket.id);
});
socket.on('reconnect', function(data) {
	logger.debug('reconect', data);
});

const wss = new WebSocket.Server({
	port: 11123
});

function hexToAscii(e) {
	var g = "";
	var f = e.length;
	var a;
	var b = "";
	for (var d = 0; d < f; d++) {
		a = e.charCodeAt(d);
		if ((47 < a && a < 58) || (96 < a && a < 103) || (64 < a && a < 71)) {
			b += e.charAt(d)
		} else {
			if (a == 120 || a == 88) {
				b = ""
			} else {
				g += e.charAt(d);
				b = ""
			}
		}
		if (b.length == 2) {
			g += String.fromCharCode(parseInt(b, 16));
			b = ""
		}
	}
	if (b != "") {
		g += String.fromCharCode(parseInt(b, 16))
	}
	return g
}

wss.on('connection', function connection(ws) {
	ws.on('close', function cleanConnection() {
		logger.debug('try clean ws close cleanConnection');
		for (key in devDataCache) {
			if ('webSocket' in devDataCache[key] && devDataCache[key]['webSocket'] == ws) {
				delete devDataCache[key].webSocket
				logger.debug('cleaned ws close cleanConnection');
			}
		}
	})
	ws.on('message', function incoming(message) {
		logger.debug('received: %s', message);
		var rev = JSON.parse(message)
		if (rev.act == 'getData') {
			procGetData()
		} else if (rev.act == 'close') {
			closeDev()
		} else if (rev.act == 'open') {
			openDev()
		}

		function procGetData() {
			if (rev.dev in devDataCache) {
				ws.send(JSON.stringify({
					dev: rev.dev,
					timestamp: parseInt(new Date().getTime() / 1000),
					dataFrame: devDataCache[rev.dev].lastData,
					status: 'ok'
				}))
			} else {
				ws.send(JSON.stringify({
					dev: rev.dev,
					timestamp: parseInt(new Date().getTime() / 1000),
					dataFrame: "no data",
					status: 'error'
				}))
			}
		}

		function procSocketIoError() {
			ws.send(JSON.stringify({
				dev: rev.dev,
				timestamp: parseInt(new Date().getTime() / 1000),
				dataFrame: "operate server offline,try later",
				status: 'error'
			}))
			socket.connect()
		}

		function closeDev() {
			if ('id' in socket) {
				socket.emit('tx', {
					cipher: false,
					rx_window: '2',
					port: 12,
					data: '8001',
					type: 'unicast',
					eui: rev.dev,
					confirmed: true
				});
				if (rev.dev in devDataCache) {
					devDataCache[rev.dev]['lastAct'] = 'close'
					devDataCache[rev.dev]['webSocket'] = ws
				} else {
					devDataCache[rev.dev] = {
						lastAct: 'close',
						webSocket: ws
					}
				}
			} else {
				procSocketIoError()
			}
		}

		function openDev() {
			if ('id' in socket) {
				socket.emit('tx', {
					cipher: false,
					rx_window: '2',
					port: 12,
					data: '8000',
					type: 'unicast',
					eui: rev.dev,
					confirmed: true
				});
				if (rev.dev in devDataCache) {
					devDataCache[rev.dev]['lastAct'] = 'open'
					devDataCache[rev.dev]['webSocket'] = ws
				} else {
					devDataCache[rev.dev] = {
						lastAct: 'open',
						webSocket: ws
					}
				}
			} else {
				procSocketIoError()
			}
		}
	});
});

logger.debug("WebSocket launched on port", wss.options.port)