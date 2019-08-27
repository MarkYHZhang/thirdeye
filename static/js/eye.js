var ws;
let webcam = document.querySelector("#webcam");
let canvas = document.querySelector("#canvas");
let ctx = canvas.getContext('2d');

var localMediaStream = null;

ws = new WebSocket("ws://"+window.location.hostname+":8889");

function see() {
    if (!localMediaStream) {
        return;``
    }

    ctx.drawImage(webcam, 0, 0, webcam.videoWidth, webcam.videoHeight, 0, 0, 640, 480);

    let dataURL = canvas.toDataURL('image/jpeg');
    var cur_path = window.location.href.split('/');
    var channel_str = cur_path[cur_path.length-1];
    // console.log(channel_str);
    // packet = JSON.stringify({"channel": "main", "frame":dataURL});
    packet = JSON.stringify({"channel": channel_str, "frame":dataURL});
    ws.send(packet);
}
var constraints = {
    video: {
        width: { min: 640 },
        height: { min: 480 }
    }
};

    navigator.mediaDevices.getUserMedia(constraints).then(function (stream) {
        webcam.srcObject = stream;
        localMediaStream = stream;
        setInterval(function(){see();},100); //10 fps
    }).catch(function (error) {
        console.log(error);
    });
