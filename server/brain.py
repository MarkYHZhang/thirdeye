import socket
import cv2
import pickle
import struct
import imutils
import numpy as np
import threading
import time


class Brain():

    def __init__(self):
        print("[INFO] loading model...")
        self.net = cv2.dnn.readNetFromCaffe("deploy.prototxt.txt", "res10_300x300_ssd_iter_140000.caffemodel")
        self.processed_frame = None
        self.processed_image = None
        threads = [
            threading.Thread(target=self.start_processing_server, args=(), kwargs={}),
            threading.Thread(target=self.start_streaming_server, args=(), kwargs={}),
        ]
        for th in threads:
            th.start()
            print(f'threads {th} started')
            th.join(0.1)

    def start_streaming_server(self):
        HOST = ''
        PORT = 8889

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print('Streaming Socket created')

        s.bind((HOST, PORT))
        print('Streaming Socket bind complete')
        s.listen(10)
        print('Streaming Socket now listening')

        while True:
            try:
                conn, addr = s.accept()
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
                while True:
                    result, frame = cv2.imencode('.jpg', self.processed_frame, encode_param)
                    data = pickle.dumps(frame, 0)
                    size = len(data)
                    conn.send(struct.pack(">L", size) + data)
                    time.sleep(1/60)
            except Exception as e:
                print(str(e))

    def start_processing_server(self):
        HOST = ''
        PORT = 8888

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print('Socket created')

        s.bind((HOST, PORT))
        print('Socket bind complete')
        s.listen(10)
        print('Socket now listening')

        while True:
            try:
                conn, addr = s.accept()

                data = b""
                payload_size = struct.calcsize(">L")
                print("payload_size: {}".format(payload_size))
                thr = None
                client_disconnected = False
                while True:
                    while len(data) < payload_size:
                        # print("Recv: {}".format(len(data)))
                        data += conn.recv(4096)
                        if not data:
                            client_disconnected = True
                            break
                    if client_disconnected:
                        break

                    # print("Done Recv: {}".format(len(data)))
                    packed_msg_size = data[:payload_size]
                    data = data[payload_size:]
                    msg_size = struct.unpack(">L", packed_msg_size)[0]
                    # print("msg_size: {}".format(msg_size))
                    while len(data) < msg_size:
                        data += conn.recv(4096)
                    frame_data = data[:msg_size]
                    data = data[msg_size:]
                    frame = pickle.loads(frame_data, fix_imports=True, encoding="bytes")
                    frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
                    if not thr or not thr.is_alive():
                        thr = threading.Thread(target=self.process, args=(frame,), kwargs={})
                        thr.start()
                    if self.processed_frame is None:
                        self.processed_frame = frame
                time.sleep(1/60)
            except Exception as e:
                print(str(e))
    
    def process(self, input_frame):
        frame = imutils.resize(input_frame, width=400)

        # grab the frame dimensions and convert it to a blob
        (h, w) = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))

        # pass the blob through the network and obtain the detections and
        # predictions
        self.net.setInput(blob)
        detections = self.net.forward()

        # loop over the detections
        for i in range(0, detections.shape[2]):
            # extract the confidence (i.e., probability) associated with the
            # prediction
            confidence = detections[0, 0, i, 2]

            # filter out weak detections by ensuring the `confidence` is
            # greater than the minimum confidence
            if confidence < 0.5:
                continue

            # compute the (x, y)-coordinates of the bounding box for the
            # object
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype("int")

            # draw the bounding box of the face along with the associated
            # probability
            text = "{:.2f}%".format(confidence * 100)
            y = startY - 10 if startY - 10 > 10 else startY + 10
            cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 0, 255), 2)
            cv2.putText(frame, text, (startX, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 2)
        self.processed_frame = frame
        resized = cv2.resize(frame, None, fx=3, fy=3)
        ret, jpeg = cv2.imencode('.jpg', resized)
        self.processed_image = jpeg.tobytes()
    
    def get_image(self):
        return self.processed_image


brain = Brain()


from flask import Flask, render_template, Response

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

def gen():
    while True:
        frame = brain.get_image()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


app.run(host='0.0.0.0')