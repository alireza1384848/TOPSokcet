from time import sleep

from TOUSocket import *


s = TOUSocket()
s.socket()
# s.bind('127.0.0.1',8000)
s.connect('127.0.0.1',9000,mss=1)
a = b"abcdefghijklmnopqrstuwxyz"
c= bytearray(len(a)+1)
c[0:len(a)] = a

s.send(c)
sleep(100)
s.close()

