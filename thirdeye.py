from flask import Flask, render_template, request, Response
from flask_socketio import SocketIO,  Namespace, emit, send
from processor import Processor
from queue import Queue


class Brain(Namespace):

    def __init__(self):
        super()
        self.channels = {}
        self.processors = {}
        self.running = {}

    def on_seeing(self, data):
        channel = data['channel']
        if channel in self.running and self.running[channel][0]:
            return
        if channel not in self.channels:
            self.channels[channel] = Queue(-1)
            self.processors[channel] = Processor()
            self.running[channel] = [True]
        self.processors[channel].process(self.running[channel], self.channels[channel], data['frame'])


import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

socketio = SocketIO(app)

brain = Brain()
brain.namespace = '/brain'
socketio.on_namespace(brain)


@app.route('/')
def index():
    return render_template('index.html')


def gen(channel):
    while True:
        if channel not in brain.channels:
            continue
        processed_results = brain.channels[channel]
        frame = processed_results.get()
        with processed_results.mutex:
            processed_results.queue.clear()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


@app.route('/video_feed')
def video_feed():
    channel = request.args.get('channel')
    if not channel:
        return
    return Response(gen(channel),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    socketio.run(app, port=8080)