import cv2
import socket
import struct
import pickle

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# client_socket.connect(('us.vpn.markyhzhang.com', 8888))
client_socket.connect(('localhost', 8888))
connection = client_socket.makefile('wb')

cam = cv2.VideoCapture(0)

cam.set(3, 400)
cam.set(4, 400)

img_counter = 0

encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]

while True:
    ret, frame = cam.read()
    result, frame = cv2.imencode('.jpg', frame, encode_param)
    data = pickle.dumps(frame, 0)
    size = len(data)

    print("{}: {}".format(img_counter, size))
    
    client_socket.send(struct.pack(">L", size) + data)
    img_counter += 1

cam.release()
