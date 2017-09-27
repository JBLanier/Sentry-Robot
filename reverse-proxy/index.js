var express = require('express');
var bodyParser = require('body-parser')
var WebSocket = require('ws');

var fs = require('fs');
var app = express();

app.use( bodyParser.json() );       // to support JSON-encoded bodies
app.use(bodyParser.urlencoded({     // to support URL-encoded bodies
  extended: true
})); 

app.get('/', function(req, res){
    console.log('GET /')
    //var html = '<html><body><form method="post" action="http://localhost:3000">Name: <input type="text" name="name" /><input type="submit" value="Submit" /></form></body>';
    res.writeHead(200, {'Content-Type': 'text/plain'});
    res.end("Howdy");
});

app.post('/newtarget_:name', function(req, res){
    console.log('POST /newtarget_:name');
    console.dir(req.params);
    var name = req.params.name;
    console.log("Name: " + name);
    res.writeHead(200, {'Content-Type': 'text/html'});
    res.end('Done');

    createSocket("ws:172.27.208.2:9000", name)

});

function createSocket(address, name) {
    socket = new WebSocket(address);
    socketName = name;
    socket.binaryType = "arraybuffer";
    socket.onopen = function() {

        socket.send(JSON.stringify({'type': 'NULL'}));
        newTarget(name, socket);
        setTimeout(() => { socket.close(); }, 7000);

    }
    socket.onmessage = function(e) {
        console.log(e);
        console.log("Unrecognized message type: " + JSON.parse(e.data).type);
        
    }
    socket.onerror = function(e) {
        console.log("Error creating WebSocket connection to " + address);
        console.log(e);
    }
    socket.onclose = function(e) {
        console.log("On Close Called: " + e);
    }
}

function newTarget(target, socket) {
    var newTarget = target
    if (newTarget == "") return;

    if (socket != null) {
        var msg = {
            'type': 'NEW_TARGET',
            'val': newTarget
        };
        socket.send(JSON.stringify(msg));
    } else {
        console.log("socket was null")
    }
}



port = 3000;
app.listen(port);
console.log('Listening at http://localhost:' + port)
