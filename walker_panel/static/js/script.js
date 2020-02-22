
var ws_connection;


function connect_websocket() {
    var ws_schema = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    ws_connection = new WebSocket(ws_schema + window.location.host + '/ws/');
}

connect_websocket();

ws_connection.onmessage = function(e) {
        var data = JSON.parse(e.data);
        console.log(data)
    };

function check_websocket_state() {
    if (ws_connection.readyState != 1) {
        ws_connection.close();
        connect_websocket();
    }
}

function send_data(data) {
    try {
        ws_connection.send(JSON.stringify(data));
    } catch (error) {
        check_websocket_state();
        setTimeout(500, send_data, data);
    }
}

// send_data({'data': 'хуй'})

$("#save-proxies").on("click", function(){
   var proxy_input = $("#proxy-input").val();
   let data = {
       'method': 'save_proxies',
       'data': proxy_input,
       'user_id': user_id
   };
   send_data(data);
});