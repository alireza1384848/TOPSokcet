from time import sleep

from TOUSocket import *
client = TOUSocket()
client.socket(mss=1024)
client.connect("127.0.0.1", 5000, window_size=4096)
client.send(b"Hello, Server!")
data = client.receive(14)
print(f"Received: {data}")
client.close()

# s = TOUSocket()
# s.socket(mss=1)
# # s.bind('127.0.0.1',8000)
# s.connect('127.0.0.1',9000,mss=1)
# a = b"abcdefghijklmnopqrstuwxyz"
# c= bytearray(len(a)+1)
# c[0:len(a)] = a
# #
# # s.send(c)
# # print(f"Message = {s.receive(9)}")
# s.close()
#
