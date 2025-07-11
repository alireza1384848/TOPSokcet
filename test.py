# from TOUPacket import TOUPacket
# from TOUSocket import *
#
#
# s = TOUSocket()
# s.socket()
# s.bind('127.0.0.1',9000)
#
# s.listen()
# conn , addr= s.accept()
#
# s.close()
# # print(f"Message = {conn.receive(25)} from {addr}")
# # a = b"salam man"
# # c= bytearray(len(a)+1)
# # c[0:len(a)] = a
# # conn.send(c)

from TOUSocket import TOUSocket
server = TOUSocket()
server.socket(mss=1024)
server.bind("127.0.0.1", 5000)
server.listen()
conn, addr = server.accept()
conn.send(b"Hello, Client!")
data = conn.receive(14)
print(f"Received : {data}")
server.close()