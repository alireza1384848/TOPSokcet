from TOUPacket import TOUPacket
from TOUSocket import *


s = TOUSocket()
s.socket()
s.bind('127.0.0.1',9000)

s.listen()
conn , addr= s.accept()

s.close()
# print(f"Message = {conn.receive(25)} from {addr}")
# a = b"salam man"
# c= bytearray(len(a)+1)
# c[0:len(a)] = a
# conn.send(c)
