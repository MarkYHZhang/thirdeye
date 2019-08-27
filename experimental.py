import asyncio
import websockets
from processor import Processor
from flask import Flask, render_template, request, Response
from queue import LifoQueue
import threading
import json

class Brain():

    def __init__(self):
        self.channels = {}
        self.processors = {}
        self.running = {}

    async def consumer_handler(self, websocket, path):
        async for message in websocket:
            data = json.loads(message)
            channel = data['channel']
            if channel in self.running and self.running[channel][0]:
                continue
            if channel not in self.channels:
                self.channels[channel] = LifoQueue(-1)
                self.processors[channel] = Processor()
                self.running[channel] = [True]
            t = threading.Thread(target=self.processors[channel].process, args=(self.running[channel], self.channels[channel], data['frame']))
            t.start()
            t.join(0)
            # self.processors[channel].process(self.running[channel], self.channels[channel], data['frame'])


brain = Brain()


def start_ws(ip='0.0.0.0', port=8889):
    start_server = websockets.serve(brain.consumer_handler, ip, port)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()


import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'


# @app.route('/')
# def index():
#     return render_template('index.html')


@app.route('/eye/<channel>')
def eye(channel):
    return render_template('eye.html')


@app.route('/')
def display():
    return render_template('display.html')


@app.route('/channels')
def channels():
    return json.dumps(list(brain.running.keys()))


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
    print("running")
    http = threading.Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': 8888})
    http.start()
    http.join(0.1)
    start_ws('0.0.0.0', 8889)
