import cv2
import socket
import struct
import pickle
import threading

class Display():

    def __init__(self,):
        self.frame = None
        threads = [
            threading.Thread(target=self.receive, args=(), kwargs={}),
            threading.Thread(target=self.view, args=(), kwargs={}),
        ]
        for th in threads:
            th.start()
            print(f'threads {th} started')
            th.join(0.1)
    
    def view(self):
        while True: 
            resized = cv2.resize(self.frame, None, fx=3, fy=3)
            cv2.imshow('ImageWindow 2', resized)
            cv2.waitKey(1)

    def receive(self):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # client_socket.connect(('us.vpn.markyhzhang.com', 8889))
        client_socket.connect(('localhost', 8889))
        data = b""
        payload_size = struct.calcsize(">L")
        while True:
            while len(data) < payload_size:
                # print("Recv: {}".format(len(data)))
                data += client_socket.recv(4096)

            # print("Done Recv: {}".format(len(data)))
            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack(">L", packed_msg_size)[0]
            # print("msg_size: {}".format(msg_size))
            while len(data) < msg_size:
                data += client_socket.recv(4096)
            frame_data = data[:msg_size]
            data = data[msg_size:]
            frame = pickle.loads(frame_data, fix_imports=True, encoding="bytes")
            self.frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

Display()
