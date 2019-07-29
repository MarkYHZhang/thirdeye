import cv2
import socket
import struct
import pickle

class Display():

    def __init__(self,):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(('localhost', 8889))
        self.view()

    def view(self):
        data = b""
        payload_size = struct.calcsize(">L")
        while True:
            while len(data) < payload_size:
                print("Recv: {}".format(len(data)))
                data += self.client_socket.recv(4096)

            print("Done Recv: {}".format(len(data)))
            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack(">L", packed_msg_size)[0]
            print("msg_size: {}".format(msg_size))
            while len(data) < msg_size:
                data += self.client_socket.recv(4096)
            frame_data = data[:msg_size]
            data = data[msg_size:]
            frame = pickle.loads(frame_data, fix_imports=True, encoding="bytes")
            frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
            cv2.imshow('ImageWindow', frame)
            cv2.waitKey(1)

Display()
