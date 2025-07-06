from TOUPacket import TOUPacket
from TOUSocket import *


s = TOUSocket()
s.socket()
s.bind('127.0.0.1',9000)

s.listen()
s.accept()


