import asyncio
import websockets
from websockets.exceptions import ConnectionClosedError
from processor import Processor
from flask import Flask, render_template, request, Response
from queue import LifoQueue
import threading
import json
import time

class Brain():

    def __init__(self):
        self.channels = {}
        self.processors = {}
        self.running = {}
        self.last_visit = {}

    def clean_disconnected_clients(self):
        t = dict(self.last_visit.items())
        for channel, last_visit in t:
            if time.time() - last_visit > 5:
                del self.last_visit[channel]
                del self.running[channel]
                del self.channels[channel]
                del self.processors[channel]

    async def consumer_handler(self, websocket, path):
        try:
            async for message in websocket:
                data = json.loads(message)
                channel = data['channel']
                if channel in self.running and self.running[channel][0]:
                    continue
                if channel not in self.channels:
                    self.channels[channel] = LifoQueue(-1)
                    self.processors[channel] = Processor()
                    self.running[channel] = [True]
                    self.last_visit[channel] = time.time()
                t = threading.Thread(target=self.processors[channel].process, args=(self.running[channel], self.channels[channel], data['frame']))
                t.start()
                t.join()
        except ConnectionClosedError:
            print('Connection closed for an eye client')
            self.clean_disconnected_clients()


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
