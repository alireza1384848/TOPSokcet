# import queue
# import time as t
# from datetime import datetime, time
# from logging import exception
# from time import sleep
#
# from TOUSendDisptcher import TOUSendDispatcher
# import threading
# import random
# from typing import Union
# from socket import socket
#
# num_ack = 0
#
# from TOUPacket import TOUPacket as packet
#
#
# class TOUConnection:
#     source_ip:str = ''
#     source_port:int = 0
#     target_ip:str = ''
#     target_port:int = 0
#     socket:socket
#     BUFFER_SIZE : int = 50000
#     mss : int = 0
#     window_size : int = 0
#     rwnd : int = 0
#     cwnd : int = 0
#     dispatcher : TOUSendDispatcher = None
#     incoming_packet : queue.Queue[packet] = queue.Queue()
#
#     SEND_BUFFER = bytearray(BUFFER_SIZE)
#     SEND_BUFFER_BASE: int =0
#     NEXT_SEQ_NUM_SEND: int =0
#     LAST_DATA_BUFFER_SEND : int =0
#     pending_packet_list : list[(int,int,t)] = []
#     ack_dict:queue.Queue = queue.Queue()
#
#     START_BUFFER_SEQNUM : int = 0
#
#     RECV_BUFFER = bytearray(BUFFER_SIZE)
#     RECV_BUFFER_BASE: int = 0
#     EXPECTED_SEQ_NUM : int = 0
#     READY_READ_POS_RECV: int =0
#     NEXT_Ack_NUM_RECV: int = 0
#     LAST_DATA_RECV: int = 0
#     out_order_packet_list : list[(int,int)] = []# seqnum ,size
#
#
#     SRTT: float = 1.0
#     RTTVAR: float = 0.5
#     RTO: float = 1.0
#     ALPHA: float = 0.125
#     BETA: float = 0.25
#
#     last_ack_freq: tuple = () # acknum , frequency
#
#     fin_ack_pack:(int,int) = (-1,-1) # seqnum , acknum
#     fin_queue : queue.Queue[packet] = queue.Queue()
#     fin_ack_recived = False
#     close_from_source = False
#     close_form_target = False
#     is_closed:bool = False
#
#     in_zero_window = False
#     last_probe_time = 0.0
#     probe_interval = 1.0
#
#     def __init__(self,sock:socket,source_ip:str, source_port:int, target_ip:str,
#                  target_port:int,r,seqnum , acknum,window_size :int=50000,buffer_size :int= 50000, mss:int=1024):
#
#         self.send_thread_running = True
#         self.source_ip = source_ip
#         self.source_port = source_port
#         self.target_ip = target_ip
#         self.target_port = target_port
#         self.BUFFER_SIZE = buffer_size
#         self.socket = sock
#         self.mss = mss
#         self.window_size = window_size
#         self.cwnd = mss
#         self.rwnd =r
#         self.dispatcher = TOUSendDispatcher(self.socket)
#         self.Next_SEQ_NUM_SEND = seqnum
#         self.START_BUFFER_SEQNUM = seqnum
#
#         self.availble_data = False
#         self.Next_Ack_NUM_RECV = acknum
#         self.EXPECTED_SEQ_NUM = acknum
#
#         var = threading.Thread(target=self.send_thread ,args=() , name="send thread").start()
#         var2 = threading.Thread(target=self.recive_thread,args=(), name="receive thread").start()
#
#         self.in_zero_window = False
#         self.last_probe_time = 0.0
#         self.probe_interval = 1.0
#
#         self.ack_dict =  queue.Queue()
#         self.last_ack_freq : tuple =()
#
#         self.is_closed = False
#
#     def add_to_ack(self,packet:packet):
#         self.ack_dict.put(packet)
#     def add_packet(self,packet:packet):
#         self.incoming_packet.put(packet)
#     def add_fin(self,packet:packet):
#         self.fin_queue.put(packet)
#
#     def write_to_receive_buffer(self ,bytearr: bytearray) :
#         if self.BUFFER_SIZE - self.LAST_DATA_BUFFER_SEND > len(bytearr):
#             self.SEND_BUFFER[self.LAST_DATA_BUFFER_SEND + 1: self.LAST_DATA_BUFFER_SEND + len(bytearr) + 1] = bytearr
#             return len(bytearr)
#         else :
#             return 0
#
#     def send(self,array: bytearray):
#         timeout = len(array)
#         current_time = t.time()
#         if not self.is_closed:
#                 while self.BUFFER_SIZE - self.LAST_DATA_BUFFER_SEND < len(array):
#                     if t.time() - current_time > timeout:
#                         raise exception(f"{datetime.now()} Receive timeout.")
#                     pass
#                 self.SEND_BUFFER[self.LAST_DATA_BUFFER_SEND: self.LAST_DATA_BUFFER_SEND + len(array)] = array
#                 self.LAST_DATA_BUFFER_SEND = self.LAST_DATA_BUFFER_SEND + len(array)
#
#     def receive (self ,length:int) -> Union[int, bytearray, None]:
#         timeout =  length
#         current_time = t.time()
#         if not self.is_closed:
#             while  self.RECV_BUFFER_BASE < length :
#                 sleep(0.01)
#                 if t.time() - current_time > timeout:
#                     raise exception(f"{datetime.now()} Receive timeout.")
#                 pass
#             data = self.RECV_BUFFER[0:length]
#             self.RECV_BUFFER = self.RECV_BUFFER[length:] + bytearray(length)
#             self.RECV_BUFFER_BASE -=length
#             return data
#     def close(self):
#         seqnum = self.Next_SEQ_NUM_SEND
#         acknum = self.Next_Ack_NUM_RECV
#         fin_pkt :packet = packet(self.source_port,
#                             self.target_port,
#                             seqnum,
#                             acknum,
#                             {'SYN': False, 'ACK': False
#                             , 'RST': False, 'FIN': True},
#                         100,
#                              bytearray()
#                             ,self.mss
#                        )
#         max_retries = 5
#         retry_count = 0
#         while retry_count < max_retries  and not self.close_from_source:
#             time = t.time()
#             self.fin_ack_pack = (acknum, seqnum +1)
#             self.dispatcher.write(fin_pkt,(self.target_ip,self.target_port))
#             #timeout
#             while not self.fin_ack_recived:
#                 if t.time() - time > 10*self.RTO:
#                     retry_count += 1
#                     break
#                 sleep(0.01)
#             if not self.fin_ack_recived:
#                 continue
#             print(f"{datetime.now()} Waiting to close Connection from {self.target_ip}:{self.target_port}")
#             self.close_from_source = True
#             break
#         current_time = t.time()
#         while self.close_from_source :
#             if t.time() - current_time > 10 * self.RTO:
#                 print(f"{datetime.now()} Target didn't Response Closing. \n {datetime.now()} Connection Closed!")
#                 self.dispatcher.turn_off()
#                 self.is_closed = True
#             elif self.close_form_target:
#                 self.dispatcher.turn_off()
#                 self.is_closed = True
#                 print(f"{datetime.now()} Connection Successfully Closed!")
#                 return
#
#             sleep(0.01)
#
#         print(f"{datetime.now()} Target didn't Response Closing. \n {datetime.now()} Connection Closed!")
#         self.is_closed = True
#
#     def close_by_rst(self):
#         """
#         Send a TCP Reset (RST) packet to the target.
#         This should be used to abort a connection.
#
#         :param addr : address to send the Rst packet to
#         """
#         seqnum = self.Next_SEQ_NUM_SEND
#         acknum = self.Next_Ack_NUM_RECV
#         rst_pkt = packet(
#             self.source_port,
#             self.target_port,
#             seqnum,
#             acknum,
#             {'SYN': False, 'ACK': False, 'RST': True, 'FIN': False},
#             window_size=self.window_size,
#             mss=self.mss,
#             payload=bytearray()
#         )
#         try:
#             self.dispatcher.write(rst_pkt, (self.target_ip,self.target_port))
#             self.is_closed = True
#             sleep(3)
#             self.dispatcher.turn_off()
#             print(f"[{datetime.now()}] Close by RST flag")
#
#         except Exception as e:
#             print(f"[{datetime.now()}] Error sending RST packet: {e}")
#
#
#     def send_thread(self):
#         while not self.is_closed:
#             if self.SEND_BUFFER_BASE < self.LAST_DATA_BUFFER_SEND:
#                 window_size = min(self.rwnd, self.cwnd)
#                 my_rwnd = self.BUFFER_SIZE - self.LAST_DATA_RECV
#                 len_send_bytes = min(window_size, self.LAST_DATA_BUFFER_SEND - self.SEND_BUFFER_BASE)
#
#                 for i in range(0,len_send_bytes,self.mss):
#                         chunk_size = min(self.mss,len_send_bytes-i)
#                         data_chunk = self.SEND_BUFFER[i+self.SEND_BUFFER_BASE:i+self.SEND_BUFFER_BASE+chunk_size]
#                         seq_num = self.START_BUFFER_SEQNUM + i
#                         pak = None
#                         if not any(seq_num == pend_seq for pend_seq,_,_ in self.pending_packet_list[:]):
#                             pak = packet(
#                                 self.source_port,
#                                 self.target_port,
#                                 seq_num,
#                                 self.Next_Ack_NUM_RECV,
#                                 {'SYN': False, 'ACK': False , 'RST': False, 'FIN': False}
#                                 ,window_size= my_rwnd
#                                 ,mss= self.mss
#                                 ,payload=data_chunk
#                             )
#                             self.pending_packet_list.append((seq_num,chunk_size,t.time()))
#                             try:
#                                 self.NEXT_SEQ_NUM_SEND = pak.seqnum + chunk_size
#                                 self.dispatcher.write(pak, (self.target_ip, self.target_port))
#                             except Exception as e:
#                                 print(f'[{datetime.now()}] error in connection send thread : {e}')
#
#                         else :
#                             for pend_seq,len,_ in self.pending_packet_list[:]:
#                                 if seq_num == pend_seq and chunk_size > len :
#                                     data_chunk = self.SEND_BUFFER[i+ self.SEND_BUFFER_BASE+len : i + self.SEND_BUFFER_BASE +len +(chunk_size - len)]
#                                     seq_num = self.START_BUFFER_SEQNUM + i +len
#                                     pak = packet(
#                                         self.source_port,
#                                         self.target_port,
#                                         seq_num,
#                                         self.Next_Ack_NUM_RECV,
#                                         {'SYN': False, 'ACK': False, 'RST': False, 'FIN': False}
#                                         , window_size=my_rwnd
#                                         , mss=self.mss
#                                         , payload=data_chunk
#                                     )
#
#
#                                     try :
#                                         self.NEXT_SEQ_NUM_SEND = pak.seqnum + chunk_size
#                                         self.dispatcher.write(pak,(self.target_ip,self.target_port))
#                                     except Exception as e:
#                                      print(f'[{datetime.now()}] error in connection send thread : {e}')
#             if self.rwnd == 0:
#                 if not self.in_zero_window:
#                     print(f"[{datetime.now()}] Entered Zero Window state.")
#                     self.in_zero_window = True
#
#                 if t.time() - self.last_probe_time >= self.probe_interval:
#                     try:
#                         probe_seq = self.START_BUFFER_SEQNUM + self.SEND_BUFFER_BASE
#                         data_chunk = bytearray()
#                         probe_pkt = packet(
#                             self.source_port,
#                             self.target_port,
#                             probe_seq,
#                             self.Next_Ack_NUM_RECV,
#                             {'SYN': False, 'ACK': False, 'RST': False, 'FIN': False},
#                             window_size= self.BUFFER_SIZE - self.LAST_DATA_RECV,
#                             mss=self.mss,
#                             payload=data_chunk
#                         )
#                         self.dispatcher.write(probe_pkt, (self.target_ip, self.target_port))
#                         self.last_probe_time = t.time()
#                         print(f"[{datetime.now()}] Zero Window Probe sent.")
#                     except Exception as e:
#                         print(f"[{datetime.now()}] Error sending zero window probe: {e}")
#             else:
#                 if self.in_zero_window:
#                     print(f"[{datetime.now()}] Exited Zero Window state.")
#                     self.in_zero_window = False
#
#             self.handel_ack()
#             sleep(0.001)
#     def handel_ack(self):
#         current_time = t.time()
#         timeout_count =0
#         try :
#             while not self.ack_dict.empty():
#                 pak = self.ack_dict.get()
#
#                 #handle duplicate ack
#                 if self.last_ack_freq != () and  self.last_ack_freq[0] == pak.acknum:
#
#                     if self.last_ack_freq[1] < 3 :
#                         self.last_ack_freq = (self.last_ack_freq[0], self.last_ack_freq[1]+1)
#
#                     #fast retransmission
#                     else :
#                         len = 0
#                         seq =0
#                         found = False
#                         for seq_num,size,time in self.pending_packet_list:
#                             if seq_num == pak.seqnum :
#                               seq = seq_num
#                               len = size
#                               found = True
#                         if not found :
#                             raise exception(f"Invalid retransmission sequence {pak.seqnum}!")
#
#                         pos = (seq - self.START_BUFFER_SEQNUM) + self.SEND_BUFFER_BASE
#                         data_chunk = self.SEND_BUFFER[pos: pos+len]
#                         pak = packet(
#                             self.source_port,
#                             self.target_port,
#                             pak.acknum,
#                             self.Next_Ack_NUM_RECV,
#                             {'SYN': False, 'ACK': False, 'RST': False, 'FIN': False}
#                             , window_size=self.rwnd
#                             , mss=self.mss
#                             , payload = data_chunk
#                         )
#
#
#                         try:
#                             self.dispatcher.write(pak, (self.target_ip, self.target_port))
#                             self.pending_packet_list = [(seq, size, ti) for seq, size, ti in self.pending_packet_list if seq != seq]
#                             self.pending_packet_list.append((seq, len, current_time))
#                         except Exception as e:
#                             print(f'[{datetime.now()}] error in connection send thread : {e}')
#                 if (pak.seqnum , pak.acknum) == self.fin_ack_pack:
#                     self.fin_ack_recived = True
#                     return
#
#                 #handle healthy ack
#                 elif (pak.acknum - self.START_BUFFER_SEQNUM) >= 0 and pak:
#                     self.SEND_BUFFER_BASE += pak.acknum - self.START_BUFFER_SEQNUM
#                     self.cwnd += self.cwnd
#                     self.rwnd = pak.window_size
#                     if self.rwnd == 0:
#                         if not self.in_zero_window:
#                             print(f"[{datetime.now()}] Entered Zero Window state.")
#                             self.in_zero_window = True
#                     self.Next_Ack_NUM_RECV = pak.seqnum
#
#                     self.last_ack_freq = (pak.acknum, 1)
#                     self.START_BUFFER_SEQNUM = pak.acknum
#                     for seq_num, chunk_size, sent_time in self.pending_packet_list[-1:]:
#                         if seq_num < pak.acknum:
#                             # rtt = current_time - sent_time
#                             # # Update SRTT and RTTVAR
#                             # self.SRTT = (1 - self.ALPHA) * self.SRTT + self.ALPHA * rtt
#                             # self.RTTVAR = (1 - self.BETA) * self.RTTVAR + self.BETA * abs(self.SRTT - rtt)
#                             # self.RTO = max(1.0, min(60.0, self.SRTT + 4 * self.RTTVAR))  # Bound RTO between 1s and 60s
#                             self.RTO = 2
#                         self.pending_packet_list = [
#                             (seq_num, chunk_size, sent_time)
#                             for seq_num, chunk_size, sent_time in self.pending_packet_list
#                             if seq_num >= pak.acknum
#                         ]
#
#
#                 #time out
#             if self.pending_packet_list:
#                     seq_num, chunk_size, sent_time = self.pending_packet_list[0]
#                     if current_time - sent_time > self.RTO and self.rwnd >= chunk_size:
#                         # Retransmit the oldest packet
#                         try:
#                             data_chunk = self.SEND_BUFFER[self.SEND_BUFFER_BASE+seq_num - self.START_BUFFER_SEQNUM : self.SEND_BUFFER_BASE+seq_num - self.START_BUFFER_SEQNUM + chunk_size]
#                             pkt = packet(
#                                 self.source_port,
#                                 self.target_port,
#                                 seq_num,
#                                 self.Next_Ack_NUM_RECV,
#                                 {'SYN': False, 'ACK': False, 'RST': False, 'FIN': False},
#                                 self.rwnd,
#                                 data_chunk,
#                                 self.mss
#                             )
#
#                             print(f"retransmition packet {pkt}")
#                             self.dispatcher.write(pkt, (self.target_ip, self.target_port))
#                             self.pending_packet_list[0] = (seq_num, chunk_size, current_time)
#                             self.cwnd = self.mss  # Reset cwnd on timeout
#                             timeout_count += 1
#                             # self.RTO = min(60.0, self.RTO * 2 ** timeout_count)  # Exponential backoff
#                         except Exception as e:
#                             print(f'[{datetime.now()}] Error in retransmission: {e}')
#
#         except Exception as e:
#             print(f'[{datetime.now()}] Error in handle_ack: {e}')
#
#     def recive_thread(self):
#         while not self.is_closed:
#             if not self.fin_queue.empty():
#                 pkt = self.fin_queue.get()
#                 self.close_form_target = True
#                 pack = packet(self.source_port
#                               , self.target_port
#                               , pkt.acknum
#                               , pkt.seqnum+1
#                               , {'SYN': False, 'ACK': True, 'RST': False, 'FIN': False}
#                               , window_size=self.BUFFER_SIZE - self.RECV_BUFFER_BASE
#                               , mss=self.mss)
#                 try:
#                     self.dispatcher.write(pack, (self.target_ip, self.target_port))
#                     self.close()
#                     continue
#                 except Exception as e:
#                     print(f'[{datetime.now()}] Error in send_ack_recv: {e}')
#             while not self.incoming_packet.empty():
#
#                 pkt = self.incoming_packet.get()
#                 #get inorder packet
#                 if self.EXPECTED_SEQ_NUM == pkt.seqnum:
#                     chunk_size = len(pkt.payload)
#
#                     self.RECV_BUFFER[self.RECV_BUFFER_BASE: self.RECV_BUFFER_BASE + chunk_size] = pkt.payload
#                     self.EXPECTED_SEQ_NUM += chunk_size
#                     self.RECV_BUFFER_BASE += chunk_size
#                     self.send_ack_recv(pkt.acknum,self.EXPECTED_SEQ_NUM)
#                 #get out_of_order packet
#                 elif pkt.seqnum > self.EXPECTED_SEQ_NUM and pkt.seqnum-self.EXPECTED_SEQ_NUM < self.BUFFER_SIZE - self.RECV_BUFFER_BASE:
#                     chunk_size = len(pkt.payload)
#                     interval =   pkt.seqnum - self.EXPECTED_SEQ_NUM
#                     self.RECV_BUFFER[self.RECV_BUFFER_BASE + interval :self.RECV_BUFFER_BASE + interval + chunk_size ] = pkt.payload
#                     self.out_order_packet_list.append((pkt.seqnum,chunk_size ))
#                #frequent packet
#                 elif pkt.seqnum < self.EXPECTED_SEQ_NUM:
#                     self.send_ack_recv(pkt.acknum,self.EXPECTED_SEQ_NUM)
#             sleep(0.001)
#     def send_ack_recv(self,seqnum,acknum):
#         for out, size in self.out_order_packet_list:
#             if acknum == out:
#                 acknum += size
#                 #self.out_order_packet_list.remove((out, size))
#         self.EXPECTED_SEQ_NUM = acknum
#         pack =  packet(self.source_port
#                       ,self.target_port
#                       ,seqnum
#                       ,acknum
#                       ,{'SYN': False, 'ACK': True, 'RST': False, 'FIN': False}
#                       ,window_size=self.BUFFER_SIZE - self.RECV_BUFFER_BASE
#                       ,mss=self.mss)
#         try :
#             self.dispatcher.write(pack, (self.target_ip, self.target_port))
#         except Exception as e:
#             print(f'[{datetime.now()}] Error in send_ack_recv: {e}')
#
#
#
#
import queue
import time as t
from datetime import datetime
from logging import exception
from time import sleep

from TOUSendDisptcher import TOUSendDispatcher
import threading
import random
from typing import Union
from socket import socket

num_ack = 0

from TOUPacket import TOUPacket as packet

class TOUConnection:
    source_ip: str = ''
    source_port: int = 0
    target_ip: str = ''
    target_port: int = 0
    socket: socket
    BUFFER_SIZE: int = 50000
    mss: int = 0
    window_size: int = 0
    rwnd: int = 0
    cwnd: int = 0
    dispatcher: TOUSendDispatcher = None
    incoming_packet: queue.Queue[packet] = queue.Queue()

    SEND_BUFFER = bytearray(BUFFER_SIZE)
    SEND_BUFFER_BASE: int = 0
    NEXT_SEQ_NUM_SEND: int = 0
    LAST_DATA_BUFFER_SEND: int = 0
    pending_packet_list: list[(int, int, t)] = []
    ack_dict: queue.Queue = queue.Queue()

    START_BUFFER_SEQNUM: int = 0

    RECV_BUFFER = bytearray(BUFFER_SIZE)
    RECV_BUFFER_BASE: int = 0
    EXPECTED_SEQ_NUM: int = 0
    READY_READ_POS_RECV: int = 0
    NEXT_Ack_NUM_RECV: int = 0
    LAST_DATA_RECV: int = 0
    out_order_packet_list: list[(int, int)] = []  # seqnum, size

    SRTT: float = 1.0
    RTTVAR: float = 0.5
    RTO: float = 1.0
    ALPHA: float = 0.125
    BETA: float = 0.25

    last_ack_freq: tuple = ()  # acknum, frequency

    fin_ack_pack: (int, int) = (-1, -1)  # seqnum, acknum
    fin_queue: queue.Queue[packet] = queue.Queue()
    fin_ack_recived = False
    close_from_source = False
    close_form_target = False
    is_closed: bool = False

    in_zero_window = False
    last_probe_time = 0.0
    probe_interval = 1.0

    def __init__(self, sock: socket, source_ip: str, source_port: int, target_ip: str,
                 target_port: int, r, seqnum, acknum, window_size: int = 50000, buffer_size: int = 50000, mss: int = 1024):
        self.send_thread_running = True
        self.source_ip = source_ip
        self.source_port = source_port
        self.target_ip = target_ip
        self.target_port = target_port
        self.BUFFER_SIZE = buffer_size
        self.socket = sock
        self.mss = mss
        self.window_size = window_size
        self.cwnd = mss
        self.rwnd = r
        self.dispatcher = TOUSendDispatcher(self.socket)
        self.Next_SEQ_NUM_SEND = seqnum
        self.START_BUFFER_SEQNUM = seqnum

        self.RECV_BUFFER = bytearray(buffer_size)
        self.SEND_BUFFER = bytearray(buffer_size)

        self.available_data = False
        self.Next_Ack_NUM_RECV = acknum
        self.EXPECTED_SEQ_NUM = acknum

        print(f"[{datetime.now()}] Connection initialized: {source_ip}:{source_port} -> {target_ip}:{target_port} | Seq: {seqnum} | Ack: {acknum}")
        var = threading.Thread(target=self.send_thread, args=(), name="send thread").start()
        var2 = threading.Thread(target=self.recive_thread, args=(), name="receive thread").start()

        self.in_zero_window = False
        self.last_probe_time = 0.0
        self.probe_interval = 1.0

        self.ack_dict = queue.Queue()
        self.last_ack_freq: tuple = ()

        self.is_closed = False

    def add_to_ack(self, packet: packet):
        self.ack_dict.put(packet)
        print(f"[{datetime.now()}] Added ACK packet to queue | Seq: {packet.seqnum} | Ack: {packet.acknum}")

    def add_packet(self, packet: packet):
        self.incoming_packet.put(packet)
        print(f"[{datetime.now()}] Added incoming packet to queue | Seq: {packet.seqnum} | Ack: {packet.acknum} | Payload size: {len(packet.payload)}")

    def add_fin(self, packet: packet):
        self.fin_queue.put(packet)
        print(f"[{datetime.now()}] Added FIN packet to queue | Seq: {packet.seqnum} | Ack: {packet.acknum}")

    def write_to_receive_buffer(self, bytearr: bytearray):
        if self.BUFFER_SIZE - self.LAST_DATA_BUFFER_SEND > len(bytearr):
            self.SEND_BUFFER[self.LAST_DATA_BUFFER_SEND + 1: self.LAST_DATA_BUFFER_SEND + len(bytearr) + 1] = bytearr
            print(f"[{datetime.now()}] Wrote {len(bytearr)} bytes to send buffer")
            return len(bytearr)
        else:
            print(f"[{datetime.now()}] Failed to write to send buffer: insufficient space")
            return 0

    def send(self, array: bytearray):
        timeout = len(array)
        current_time = t.time()
        if not self.is_closed:
            while self.BUFFER_SIZE - self.LAST_DATA_BUFFER_SEND < len(array):
                if t.time() - current_time > timeout:
                    print(f"[{datetime.now()}] Send timeout: buffer full")
                    raise exception(f"[{datetime.now()}] Send timeout.")
                pass
            self.SEND_BUFFER[self.LAST_DATA_BUFFER_SEND: self.LAST_DATA_BUFFER_SEND + len(array)] = array
            self.LAST_DATA_BUFFER_SEND = self.LAST_DATA_BUFFER_SEND + len(array)
            print(f"[{datetime.now()}] Sent {len(array)} bytes to send buffer")

    def receive(self, length: int) -> Union[int, bytearray, None]:
        timeout = length
        current_time = t.time()
        if not self.is_closed:
            while self.RECV_BUFFER_BASE < length:
                sleep(0.01)
                if t.time() - current_time > timeout:
                    print(f"[{datetime.now()}] Receive timeout: insufficient data")
                    raise exception(f"[{datetime.now()}] Receive timeout.")
                pass
            data = self.RECV_BUFFER[0:length]
            self.RECV_BUFFER = self.RECV_BUFFER[length:] + bytearray(length)
            self.RECV_BUFFER_BASE -= length
            print(f"[{datetime.now()}] Received {length} bytes from buffer")
            return data

    def close(self):
        seqnum = self.Next_SEQ_NUM_SEND
        acknum = self.Next_Ack_NUM_RECV
        fin_pkt: packet = packet(self.source_port,
                                 self.target_port,
                                 seqnum,
                                 acknum,
                                 {'SYN': False, 'ACK': False, 'RST': False, 'FIN': True},
                                 100,
                                 bytearray(),
                                 self.mss)
        max_retries = 5
        retry_count = 0
        print(f"[{datetime.now()}] Initiating connection close from {self.source_ip}:{self.source_port}")
        while retry_count < max_retries and not self.close_from_source:
            time = t.time()
            self.fin_ack_pack = (acknum, seqnum + 1)
            self.dispatcher.write(fin_pkt, (self.target_ip, self.target_port))
            print(f"[{datetime.now()}] Sent FIN packet | Seq: {seqnum} | Ack: {acknum}")
            while not self.fin_ack_recived:
                if t.time() - time > 10 * self.RTO:
                    retry_count += 1
                    print(f"[{datetime.now()}] FIN packet retry {retry_count}/{max_retries}")
                    break
                sleep(0.01)
            if not self.fin_ack_recived:
                continue
            print(f"[{datetime.now()}] Waiting for target to close connection from {self.target_ip}:{self.target_port}")
            self.close_from_source = True
            break
        current_time = t.time()
        while self.close_from_source:
            if t.time() - current_time > 10 * self.RTO:
                print(f"[{datetime.now()}] Target didn't respond to FIN. Connection closed!")
                self.dispatcher.turn_off()
                self.is_closed = True
            elif self.close_form_target:
                self.dispatcher.turn_off()
                self.is_closed = True
                print(f"[{datetime.now()}] Connection successfully closed!")
                return
            sleep(0.01)
        print(f"[{datetime.now()}] Target didn't respond to FIN. Connection closed!")
        self.is_closed = True

    def close_by_rst(self):
        seqnum = self.Next_SEQ_NUM_SEND
        acknum = self.Next_Ack_NUM_RECV
        rst_pkt = packet(
            self.source_port,
            self.target_port,
            seqnum,
            acknum,
            {'SYN': False, 'ACK': False, 'RST': True, 'FIN': False},
            window_size=self.window_size,
            mss=self.mss,
            payload=bytearray()
        )
        try:
            self.dispatcher.write(rst_pkt, (self.target_ip, self.target_port))
            self.is_closed = True
            sleep(3)
            self.dispatcher.turn_off()
            print(f"[{datetime.now()}] Connection closed by RST | Seq: {seqnum} | Ack: {acknum}")
        except Exception as e:
            print(f"[{datetime.now()}] Error sending RST packet: {e}")

    def send_thread(self):
        while not self.is_closed:
            if self.SEND_BUFFER_BASE < self.LAST_DATA_BUFFER_SEND:
                window_size = min(self.rwnd, self.cwnd)
                my_rwnd = self.BUFFER_SIZE - self.LAST_DATA_RECV
                len_send_bytes = min(window_size, self.LAST_DATA_BUFFER_SEND - self.SEND_BUFFER_BASE)

                for i in range(0, len_send_bytes, self.mss):
                    chunk_size = min(self.mss, len_send_bytes - i)
                    data_chunk = self.SEND_BUFFER[i + self.SEND_BUFFER_BASE:i + self.SEND_BUFFER_BASE + chunk_size]
                    seq_num = self.START_BUFFER_SEQNUM + i
                    pak = None
                    if not any(seq_num == pend_seq for pend_seq, _, _ in self.pending_packet_list[:]):
                        pak = packet(
                            self.source_port,
                            self.target_port,
                            seq_num,
                            self.Next_Ack_NUM_RECV,
                            {'SYN': False, 'ACK': False, 'RST': False, 'FIN': False},
                            window_size=my_rwnd,
                            mss=self.mss,
                            payload=data_chunk
                        )
                        self.pending_packet_list.append((seq_num, chunk_size, t.time()))
                        try:
                            self.NEXT_SEQ_NUM_SEND = pak.seqnum + chunk_size
                            self.dispatcher.write(pak, (self.target_ip, self.target_port))
                            print(f"[{datetime.now()}] Sent data packet | Seq: {seq_num} | Size: {chunk_size}")
                        except Exception as e:
                            print(f"[{datetime.now()}] Error in send thread: {e}")
                    else:
                        for pend_seq, len, _ in self.pending_packet_list[:]:
                            if seq_num == pend_seq and chunk_size > len:
                                data_chunk = self.SEND_BUFFER[i + self.SEND_BUFFER_BASE + len: i + self.SEND_BUFFER_BASE + len + (chunk_size - len)]
                                seq_num = self.START_BUFFER_SEQNUM + i + len
                                pak = packet(
                                    self.source_port,
                                    self.target_port,
                                    seq_num,
                                    self.Next_Ack_NUM_RECV,
                                    {'SYN': False, 'ACK': False, 'RST': False, 'FIN': False},
                                    window_size=my_rwnd,
                                    mss=self.mss,
                                    payload=data_chunk
                                )
                                try:
                                    self.NEXT_SEQ_NUM_SEND = pak.seqnum + chunk_size
                                    self.dispatcher.write(pak, (self.target_ip, self.target_port))
                                    print(f"[{datetime.now()}] Sent partial data packet | Seq: {seq_num} | Size: {chunk_size - len}")
                                except Exception as e:
                                    print(f"[{datetime.now()}] Error in send thread: {e}")
            if self.rwnd == 0:
                if not self.in_zero_window:
                    print(f"[{datetime.now()}] Entered Zero Window state")
                    self.in_zero_window = True
                if t.time() - self.last_probe_time >= self.probe_interval:
                    try:
                        probe_seq = self.START_BUFFER_SEQNUM + self.SEND_BUFFER_BASE
                        data_chunk = bytearray()
                        probe_pkt = packet(
                            self.source_port,
                            self.target_port,
                            probe_seq,
                            self.Next_Ack_NUM_RECV,
                            {'SYN': False, 'ACK': False, 'RST': False, 'FIN': False},
                            window_size=self.BUFFER_SIZE - self.LAST_DATA_RECV,
                            mss=self.mss,
                            payload=data_chunk
                        )
                        self.dispatcher.write(probe_pkt, (self.target_ip, self.target_port))
                        self.last_probe_time = t.time()
                        print(f"[{datetime.now()}] Sent Zero Window Probe | Seq: {probe_seq}")
                    except Exception as e:
                        print(f"[{datetime.now()}] Error sending Zero Window Probe: {e}")
            else:
                if self.in_zero_window:
                    print(f"[{datetime.now()}] Exited Zero Window state")
                    self.in_zero_window = False
            self.handel_ack()
            sleep(0.001)

    def handel_ack(self):
        current_time = t.time()
        timeout_count = 0
        try:
            while not self.ack_dict.empty():
                pak = self.ack_dict.get()
                print(f"[{datetime.now()}] Processing ACK | Seq: {pak.seqnum} | Ack: {pak.acknum}")
                if self.last_ack_freq != () and self.last_ack_freq[0] == pak.acknum:
                    if self.last_ack_freq[1] < 3:
                        self.last_ack_freq = (self.last_ack_freq[0], self.last_ack_freq[1] + 1)
                        print(f"[{datetime.now()}] Duplicate ACK detected | Ack: {pak.acknum} | Count: {self.last_ack_freq[1]}")
                    else:
                        len = 0
                        seq = 0
                        found = False
                        for seq_num, size, time in self.pending_packet_list:
                            if seq_num == pak.seqnum:
                                seq = seq_num
                                len = size
                                found = True
                        if not found:
                            print(f"[{datetime.now()}] Invalid retransmission sequence {pak.seqnum}")
                            raise exception(f"[{datetime.now()}] Invalid retransmission sequence {pak.seqnum}")
                        pos = (seq - self.START_BUFFER_SEQNUM) + self.SEND_BUFFER_BASE
                        data_chunk = self.SEND_BUFFER[pos: pos + len]
                        pak = packet(
                            self.source_port,
                            self.target_port,
                            pak.acknum,
                            self.Next_Ack_NUM_RECV,
                            {'SYN': False, 'ACK': False, 'RST': False, 'FIN': False},
                            window_size=self.rwnd,
                            mss=self.mss,
                            payload=data_chunk
                        )
                        try:
                            self.dispatcher.write(pak, (self.target_ip, self.target_port))
                            self.pending_packet_list = [(seq, size, ti) for seq, size, ti in self.pending_packet_list if seq != seq]
                            self.pending_packet_list.append((seq, len, current_time))
                            print(f"[{datetime.now()}] Fast retransmission | Seq: {pak.acknum} | Size: {len}")
                        except Exception as e:
                            print(f"[{datetime.now()}] Error in fast retransmission: {e}")
                if (pak.seqnum, pak.acknum) == self.fin_ack_pack:
                    self.fin_ack_recived = True
                    print(f"[{datetime.now()}] FIN ACK received | Seq: {pak.seqnum} | Ack: {pak.acknum}")
                    return
                elif (pak.acknum - self.START_BUFFER_SEQNUM) >= 0 and pak:
                    self.SEND_BUFFER_BASE += pak.acknum - self.START_BUFFER_SEQNUM
                    self.cwnd += self.cwnd
                    self.rwnd = pak.window_size
                    if self.rwnd == 0:
                        if not self.in_zero_window:
                            print(f"[{datetime.now()}] Entered Zero Window state")
                            self.in_zero_window = True
                    self.Next_Ack_NUM_RECV = pak.seqnum
                    self.last_ack_freq = (pak.acknum, 1)
                    self.START_BUFFER_SEQNUM = pak.acknum
                    for seq_num, chunk_size, sent_time in self.pending_packet_list[-1:]:
                        if seq_num < pak.acknum:
                            rtt = current_time - sent_time
                            # Update SRTT and RTTVAR
                            self.SRTT = (1 - self.ALPHA) * self.SRTT + self.ALPHA * rtt
                            self.RTTVAR = (1 - self.BETA) * self.RTTVAR + self.BETA * abs(self.SRTT - rtt)
                            self.RTO = max(1.0, min(60.0, self.SRTT + 4 * self.RTTVAR))
                        self.pending_packet_list = [
                            (seq_num, chunk_size, sent_time)
                            for seq_num, chunk_size, sent_time in self.pending_packet_list
                            if seq_num >= pak.acknum
                        ]
                    print(f"[{datetime.now()}] ACK processed | New base: {self.SEND_BUFFER_BASE} | New cwnd: {self.cwnd}")
            if self.pending_packet_list:
                seq_num, chunk_size, sent_time = self.pending_packet_list[0]
                if current_time - sent_time > self.RTO and self.rwnd >= chunk_size:
                    try:
                        data_chunk = self.SEND_BUFFER[self.SEND_BUFFER_BASE + seq_num - self.START_BUFFER_SEQNUM: self.SEND_BUFFER_BASE + seq_num - self.START_BUFFER_SEQNUM + chunk_size]
                        pkt = packet(
                            self.source_port,
                            self.target_port,
                            seq_num,
                            self.Next_Ack_NUM_RECV,
                            {'SYN': False, 'ACK': False, 'RST': False, 'FIN': False},
                            self.rwnd,
                            data_chunk,
                            self.mss
                        )
                        print(f"[{datetime.now()}] Retransmitting packet | Seq: {seq_num} | Size: {chunk_size}")
                        self.dispatcher.write(pkt, (self.target_ip, self.target_port))
                        self.pending_packet_list[0] = (seq_num, chunk_size, current_time)
                        self.cwnd = self.mss
                        timeout_count += 1
                        self.RTO = min(60.0, self.RTO * 2 ** timeout_count)
                    except Exception as e:
                        print(f"[{datetime.now()}] Error in retransmission: {e}")
        except Exception as e:
            print(f"[{datetime.now()}] Error in handle_ack: {e}")

    def recive_thread(self):
        while not self.is_closed:
            if not self.fin_queue.empty():
                pkt = self.fin_queue.get()
                self.close_form_target = True
                pack = packet(self.source_port,
                              self.target_port,
                              pkt.acknum,
                              pkt.seqnum + 1,
                              {'SYN': False, 'ACK': True, 'RST': False, 'FIN': False},
                              window_size=self.BUFFER_SIZE - self.RECV_BUFFER_BASE,
                              mss=self.mss)
                try:
                    self.dispatcher.write(pack, (self.target_ip, self.target_port))
                    print(f"[{datetime.now()}] Sent ACK for FIN | Seq: {pkt.acknum} | Ack: {pkt.seqnum + 1}")
                    self.close()
                    continue
                except Exception as e:
                    print(f"[{datetime.now()}] Error in send_ack_recv: {e}")

            while not self.incoming_packet.empty():
                pkt = self.incoming_packet.get()
                #inorder
                if self.EXPECTED_SEQ_NUM == pkt.seqnum:
                    chunk_size = len(pkt.payload)
                    self.RECV_BUFFER[self.RECV_BUFFER_BASE: self.RECV_BUFFER_BASE + chunk_size] = pkt.payload
                    self.EXPECTED_SEQ_NUM += chunk_size
                    self.RECV_BUFFER_BASE += chunk_size
                    print(f"[{datetime.now()}] Received in-order packet EXPECTED_SEQ_NUM = {self.EXPECTED_SEQ_NUM} :RECV_BUFFER_BASE:{self.RECV_BUFFER_BASE }| Seq: {pkt.seqnum} | Size: {chunk_size} |payload = {pkt.payload}")
                    print(f'{self.RECV_BUFFER[:30]}')
                    self.send_ack_recv(pkt.acknum, self.EXPECTED_SEQ_NUM)

                #out of order
                elif pkt.seqnum > self.EXPECTED_SEQ_NUM and pkt.seqnum - self.EXPECTED_SEQ_NUM < self.BUFFER_SIZE - self.RECV_BUFFER_BASE:
                    chunk_size = len(pkt.payload)
                    interval = pkt.seqnum - self.EXPECTED_SEQ_NUM

                    self.RECV_BUFFER[self.RECV_BUFFER_BASE + interval: self.RECV_BUFFER_BASE + interval + chunk_size] = pkt.payload
                    self.out_order_packet_list.append((pkt.seqnum, chunk_size))
                    print(f"[{datetime.now()}] Received out-of-order packet | Seq: {pkt.seqnum} | Size: {chunk_size} |payload = {pkt.payload}")
                elif pkt.seqnum < self.EXPECTED_SEQ_NUM:
                    print(f"[{datetime.now()}] Received duplicate packet | Seq: {pkt.seqnum}")
                    self.send_ack_recv(pkt.acknum, self.EXPECTED_SEQ_NUM)
            sleep(0.001)

    def send_ack_recv(self, seqnum, acknum):
        for out, size in self.out_order_packet_list:
            if acknum == out:
                acknum += size
        self.RECV_BUFFER_BASE += (acknum - self.EXPECTED_SEQ_NUM)
        self.EXPECTED_SEQ_NUM = acknum

        pack = packet(self.source_port,
                      self.target_port,
                      seqnum,
                      acknum,
                      {'SYN': False, 'ACK': True, 'RST': False, 'FIN': False},
                      window_size=self.BUFFER_SIZE - self.RECV_BUFFER_BASE,
                      mss=self.mss)
        try:
            self.dispatcher.write(pack, (self.target_ip, self.target_port))
            print(f"[{datetime.now()}] Sent ACK | Seq: {seqnum} | Ack: {acknum}")
        except Exception as e:
            print(f"[{datetime.now()}] Error in send_ack_recv: {e}")