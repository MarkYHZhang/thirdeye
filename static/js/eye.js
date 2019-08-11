var socket;
$(document).ready(function () {
    let webcam = document.querySelector("#webcam");
    let canvas = document.querySelector("#canvas");
    let ctx = canvas.getContext('2d');

    var localMediaStream = null;

    socket = io("/brain");

    function see() {
        if (!localMediaStream) {
            return;
        }

        ctx.drawImage(webcam, 0, 0, webcam.videoWidth, webcam.videoHeight, 0, 0, 640, 480);

        let dataURL = canvas.toDataURL('image/jpeg');
        socket.emit('seeing', data={"channel": "main", "frame":dataURL});
    }

    socket.on('connect', function () {
        console.log('Connected!');
    });

    var constraints = {
        video: {
            width: { min: 640 },
            height: { min: 480 }
        }
    };

    navigator.mediaDevices.getUserMedia(constraints).then(function (stream) {
        webcam.srcObject = stream;
        localMediaStream = stream;
        setInterval(function(){see();},10);
    }).catch(function (error) {
        console.log(error);
    });
});
