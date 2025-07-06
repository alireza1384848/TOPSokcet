from time import sleep

from TOUSocket import *


s = TOUSocket()
s.socket()
# s.bind('127.0.0.1',8000)
s.connect('127.0.0.1',9000)
sleep(100000)