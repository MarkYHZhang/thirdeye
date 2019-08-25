var ws;
$(document).ready(function () {
    let webcam = document.querySelector("#webcam");
    let canvas = document.querySelector("#canvas");
    let ctx = canvas.getContext('2d');

    var localMediaStream = null;

    ws = new WebSocket("ws://127.0.0.1:8000/");

    function see() {
        if (!localMediaStream) {
            return;``
        }

        ctx.drawImage(webcam, 0, 0, webcam.videoWidth, webcam.videoHeight, 0, 0, 640, 480);

        let dataURL = canvas.toDataURL('image/jpeg');
        packet = JSON.stringify({"channel": "main", "frame":dataURL});
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
});
