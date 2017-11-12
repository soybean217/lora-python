var wsUri = "ws://123.207.44.110:11123/ws";
var input = "";
var output;
var isOpen = false;
var websocket;

function init() {
  output = document.getElementById("output");
  openWebSocket('');
}

function openWebSocket(data) {
  websocket = new WebSocket(wsUri);
  websocket.onopen = function(evt) {
    onOpen(evt)
    if (data && data.length > 0) {
      writeToScreen("SENT: " + data);
      websocket.send(data)
    }
  };
  websocket.onclose = function(evt) {
    onClose(evt)
  };
  websocket.onmessage = function(evt) {
    onMessage(evt)
  };
  websocket.onerror = function(evt) {
    onError(evt)
  };
}

function onOpen(evt) {
  writeToScreen("CONNECTED");
  isOpen = true;
  // doSend(input); 
}

function onClose(evt) {
  writeToScreen("DISCONNECTED");
  isOpen = false;
}

function onMessage(evt) {
  console.log(evt);
  writeToScreen('<span style="color: blue;">RESPONSE: ' + evt.data + '</span>');
  // websocket.close(); 
}

function onError(evt) {
  writeToScreen('<span style="color: red;">ERROR:</span> ' + evt.data);
}

function doSend(message) {
  if (!isOpen) {
    openWebSocket(message)
  } else {
    writeToScreen("SENT: " + message);
    websocket.send(message);
  }
}

function writeToScreen(message) {
  // var pre = document.createElement("p");
  // pre.style.wordWrap = "break-word";
  // pre.innerHTML = message;
  // output.appendChild(pre);
  output.innerHTML = (new Date()).toString() + ":" + message + "<br>" + output.innerHTML
}

function sendMessage() {
  input = document.getElementById("input").value;
  doSend(input);
}

window.addEventListener("load", init, false);