# import socket
# import queue
# import threading
# from datetime import datetime
# from time import sleep
#
# from TOUPacket import TOUPacket as packet
#
# class TOUSendDispatcher:
#     udp_socket:socket = None
#     is_on = True
#     list_ban_conn = []
#     packet_queue:queue.Queue =queue.Queue()
#     def __init__(self,usocket:socket):
#         self.udp_socket =usocket
#         var = threading.Thread(target=self.send, args=(), name='Dispachter').start()
#
#     def write(self,pac:packet , addr):
#         self.packet_queue.put((pac, addr))
#     def turn_off(self):
#         self.is_on = False
#     def delete_packet_conn(self,addr):
#         self.list_ban_conn.append(addr)
#
#     def send(self):
#         while self.is_on:
#                 pac = None
#                 if not self.packet_queue.empty():
#                     pac = self.packet_queue.get()
#                 else : continue
#                 print(f"{datetime.now()}: send packet :address:{pac[1]}: seqnum :{pac[0].seqnum}: acknum : {pac[0].acknum}: payload : {pac[0].payload}")
#                 if pac[1] not in self.list_ban_conn and self.is_on:
#                     self.udp_socket.sendto(pac[0].to_bytes(), pac[1])
#                     self.list_ban_conn.clear()
#                 sleep(0.001)

import socket
import queue
import threading
from datetime import datetime
from time import sleep

from TOUPacket import TOUPacket as packet

class TOUSendDispatcher:
    udp_socket: socket = None
    is_on = True
    list_ban_conn = []
    packet_queue: queue.Queue = queue.Queue()

    def __init__(self, usocket: socket):
        self.udp_socket = usocket
        print(f"[{datetime.now()}] Dispatcher initialized for socket")
        var = threading.Thread(target=self.send, args=(), name='Dispatcher').start()

    def write(self, pac: packet, addr):
        self.packet_queue.put((pac, addr))
        print(f"[{datetime.now()}] Queued packet for sending to {addr} | Seq: {pac.seqnum} | Ack: {pac.acknum} | Payload size: {len(pac.payload)}")

    def turn_off(self):
        self.is_on = False
        print(f"[{datetime.now()}] Dispatcher turned off")

    def delete_packet_conn(self, addr):
        self.list_ban_conn.append(addr)
        print(f"[{datetime.now()}] Connection {addr} added to ban list")

    def send(self):
        while self.is_on:
            pac = None
            if not self.packet_queue.empty():
                pac = self.packet_queue.get()
            else:
                continue
            print(f"[{datetime.now()}] Sending packet to {pac[1]} \n| Seq: {pac[0].seqnum} \n| Ack: {pac[0].acknum} \n| Flags: {pac[0].flag} \n| Payload: {pac[0].payload}")
            if pac[1] not in self.list_ban_conn and self.is_on:
                self.udp_socket.sendto(pac[0].to_bytes(), pac[1])
                print(f"[{datetime.now()}] Packet sent successfully to {pac[1]}")
                self.list_ban_conn.clear()
                print(f"[{datetime.now()}] Ban list cleared")
            sleep(0.001)