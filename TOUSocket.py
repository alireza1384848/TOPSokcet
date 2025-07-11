
from datetime import datetime
import queue
import socket
import threading
import random
from logging import exception
from time import sleep

from TOUSendDisptcher import TOUSendDispatcher as Dispatcher
from TOUConnection import TOUConnection as Connection
from TOUPacket import TOUPacket as packet

MTU = 1500
Num_packet = 0
counter = 0

class TOUSocket:
    src_ip: str = ''
    src_port: int = 0
    can_work = True
    remote_addr: str = ''
    remote_port: int = 0
    udp_socket: socket.socket = None
    accept_queue: queue.Queue = queue.Queue()
    connection_dict = dict[(str, int), (Connection, bool)]
    server_port: int = 0
    ack_dict = dict[(str, int), int]
    is_closed: bool = False
    is_server: bool = False
    is_client: bool = False
    mss: int = 1024
    dispacher: Dispatcher = None
    closing = False
    connection_client: Connection

    def __init__(self) -> None:
        self.closing = None
        self.ack_dict = {}
        self.connection_dict = {}
        print(f"[{datetime.now()}] TOUSocket initialized")

    def generate_seq(self):
        a = random.randint(0, 2 ** 20 - 1)
        while a in self.ack_dict.values():
            a = random.randint(0, 2 ** 32 - 1)
        print(f"[{datetime.now()}] Generated sequence number: {a}")
        return a

    def socket(self, mss=1024):
        self.mss = mss
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print(f"[{datetime.now()}] UDP socket created with MSS: {mss}")

    def bind(self, ipaddr, port):
        """
          bind  ipaddress and port on TOPSocket
          :param ipaddr: ip address
          :param port: port number
        """
        if self.udp_socket is not None:
            print(f"[{datetime.now()}] Binding to {ipaddr}:{port}")
            self.udp_socket.bind((ipaddr, port))
            self.src_ip = ipaddr
            self.src_port = port
        else:
            raise Exception('UDP socket not initialized')

    def listen(self, accept_queue_size=3):
        """
                 listen on a socket to make a connection

                 :param accept_queue_size: maximum number of  connections want to accept
        """
        if not self.is_client:
            self.is_server = True
            self.accept_queue = queue.Queue(accept_queue_size)
            self.dispacher = Dispatcher(self.udp_socket)
            print(f"[{datetime.now()}] Listening on {self.src_ip}:{self.src_port} with queue size {accept_queue_size}")
            t = threading.Thread(target=self.buffering_thread_server, args=(), name='buffering_thread_server')
            t.start()

    def accept(self):
        """
                   return connection and accept it
                   :returns: TOPConnection , ipaddr and port
        """
        try:
            conn, addr = self.accept_queue.get(timeout=10)
            self.connection_dict[addr] = (conn, True)
            print(f"[{datetime.now()}] Accepted connection from {addr}")
            return conn, addr
        except queue.Empty:
            print(f"[{datetime.now()}] No connection found in accept queue")
            raise Exception('No connection found.')

    def connect(self, ipaddr, port, window_size=4096, mss=1024):
        if self.is_server:
            print(f"[{datetime.now()}] Connect attempt failed: socket is in server mode")
            raise exception("This is a client_method but your socket is server.")
        self.is_client = True
        try:
            self.udp_socket.getsockname()
        except socket.error:
            self.udp_socket.bind(('0.0.0.0', 0))
        self.src_ip, self.src_port = self.udp_socket.getsockname()
        randseq = self.generate_seq()
        syn_packet = packet(self.src_port,
                            port,
                            randseq,
                            0,
                            {'SYN': True, 'ACK': False, 'RST': False, 'FIN': False},
                            window_size,
                            mss=mss)
        self.udp_socket.sendto(syn_packet.to_bytes(), (ipaddr, port))
        print(f"[{datetime.now()}] Sent SYN packet to {ipaddr}:{port} | Seq: {randseq}")
        try:
            rwnd = 0
            self.udp_socket.settimeout(10)
            recv_byte = self.udp_socket.recvfrom(MTU)
            pack = packet.from_bytes(recv_byte)
            ack_packet = None
            if pack.acknum == randseq + 1:
                rwnd = pack.window_size
                ack_packet = packet(self.src_port,
                                    port,
                                    randseq + 1,
                                    pack.seqnum,
                                    {'SYN': False, 'ACK': True, 'RST': False, 'FIN': False},
                                    window_size,
                                    mss=mss)
            self.udp_socket.sendto(ack_packet.to_bytes(), (ipaddr, port))
            print(f"[{datetime.now()}] Sent ACK for SYN-ACK | Seq: {randseq + 1} | Ack: {pack.seqnum}")
            self.connection_client = Connection(self.udp_socket, self.src_ip, self.src_port,
                                                ipaddr, port, rwnd, pack.acknum, pack.seqnum, window_size, mss=mss)
            t = threading.Thread(target=self.buffering_thread_client, args=(), name='buffering_thread_client')
            t.start()
            print(f"[{datetime.now()}] Client connected to {ipaddr}:{port}")
        except socket.timeout as e:
            print(f"[{datetime.now()}] Connection timed out: server didn't respond")
            raise exception("Socket timed out.")
        except exception as e:
            print(f"[{datetime.now()}] Error during connection: {e}")
            self.is_client = False
            raise exception(f"An undefined error occurred: {e}")

    def send(self, array: bytearray):
        if self.is_client:
            self.connection_client.send(array)
            print(f"[{datetime.now()}] Sent {len(array)} bytes to {self.connection_client.target_ip}:{self.connection_client.target_port}")

    def receive(self, length: int):
        if self.is_client:
            data = self.connection_client.receive(length)
            print(f"[{datetime.now()}] Received {len(data)} bytes from {self.connection_client.target_ip}:{self.connection_client.target_port}")
            return data

    def close(self):
        if self.is_server:
            print(f"[{datetime.now()}] Server is closing...")
            self.can_work = False
            for conn, status in self.connection_dict.values():
                if not status:
                    conn.close_by_rst()
        elif self.is_client:
            print(f"[{datetime.now()}] Client is closing...")
            self.connection_client.close()

    def send_rst_packet(self, addr: tuple):
        """
             Send a TCP Reset (RST) packet to the target.
             This should be used to abort a connection.

             :param addr : address to send the Rst packet to
        """
        rst_pkt = packet(
            self.src_port,
            addr[1],
            0,
            0,
            {'SYN': False, 'ACK': False, 'RST': True, 'FIN': False},
            window_size=10,
            mss=self.mss,
            payload=bytearray()
        )
        try:
            self.udp_socket.sendto(rst_pkt.to_bytes(), (addr[0], addr[1]))
            print(f"[{datetime.now()}] Sent RST packet to {addr}")
        except Exception as e:
            print(f"[{datetime.now()}] Error sending RST packet: {e}")

    def buffering_thread_server(self):
        """
                this function should run as a thread
                Receive data from active connections and deliver it to the corresponding connections (demultiplexing operation)

                •
                Check SYN packets received for establishing a new connection and perform the handshake operation if valid or not

                And finally, accept them into the queue after success

                Identify invalid packets or packets from unknown connections, and ignore or respond appropriately (e.g., RST packet) to them.
        """
        print(f"[{datetime.now()}] Buffering thread started on {self.src_ip}:{self.src_port}")
        while not self.is_closed:
            dellist = []
            for conn in self.connection_dict.keys():
                if self.connection_dict[conn][0].is_closed:
                    dellist.append(conn)
            for conn in dellist:
                self.connection_dict.pop(conn, None)
                self.dispacher.delete_packet_conn(conn)
                print(f"[{datetime.now()}] Removed closed connection {conn}")
            try:
                self.udp_socket.settimeout(10)
                recv_bytes, addr = self.udp_socket.recvfrom(1024)
                pack = None
                try:
                    #finish connection
                    if not self.can_work and len(self.connection_dict) == 0:
                        self.is_closed = True
                        self.dispacher.turn_off()
                    pack = packet.from_bytes(recv_bytes)
                    print(f"[{datetime.now()}] Received packet from {addr} \n| Seq: {pack.seqnum} \n| Ack: {pack.acknum} \n| Flags: {pack.flag} \n| Payload : {pack.payload}")
                    randseq = self.generate_seq()


                    # if client want to establish a connection
                    if pack.is_sync() and not pack.is_ack() and not pack.is_fin() and not pack.is_rst() and self.can_work:
                        ack_apk = packet(pack.dest_port,
                                         pack.source_port,
                                         randseq,
                                         pack.seqnum + 1,
                                         {'SYN': True, 'ACK': True, 'RST': False, 'FIN': False},
                                         pack.window_size, mss=pack.mss)
                        self.ack_dict[addr] = randseq
                        self.dispacher.write(ack_apk, addr)
                        print(f"[{datetime.now()}] Sent SYN-ACK to {addr} | Seq: {randseq} | Ack: {pack.seqnum + 1}")

                    # establish connection and add client to accept list
                    elif addr in self.ack_dict.keys() and self.can_work:
                        if pack.is_ack() and not pack.is_fin() and not pack.is_rst() and not pack.is_sync():
                            if pack.acknum == self.ack_dict[addr]:
                                conn = Connection(self.udp_socket,
                                                  self.src_ip,
                                                  self.src_port,
                                                  addr[0],
                                                  addr[1],
                                                  pack.window_size,
                                                  pack.acknum,
                                                  pack.seqnum)
                                self.connection_dict[addr] = (conn, False)
                                self.accept_queue.put((conn, addr))
                                print(f"[{datetime.now()}] Connection accepted from {addr}")
                                self.ack_dict.pop(addr)
                    # send packet to appropriate connection.
                    elif addr in self.connection_dict.keys():
                        if pack.is_ack():
                            self.connection_dict[addr][0].add_to_ack(pack)
                            print(f"[{datetime.now()}] Forwarded ACK packet to connection {addr}")
                        elif pack.is_fin():
                            self.connection_dict[addr][0].add_fin(pack)
                            print(f"[{datetime.now()}] Forwarded FIN packet to connection {addr}")
                        elif pack.is_rst():
                            self.connection_dict[addr][0].is_closed = True
                            self.connection_dict[addr][0].dispatcher.turn_off()
                            print(f"[{datetime.now()}] Connection closed by RST from {addr}")
                        else:
                            # self.connection_dict[addr][0].add_packet(pack)
                            # print(f"[{datetime.now()}] Forwarded data packet to connection {addr}")
                            ### DROP PACKET
                            global Num_packet
                            Num_packet += 1
                            if Num_packet == 5:
                                print(f"[{datetime.now()}] Forwarded data packet to connection {addr}")
                            else:
                                self.connection_dict[addr][0].add_packet(pack)
                    else:
                        print(f"[{datetime.now()}] Unknown packet from {addr} | Seq: {pack.seqnum} | Ack: {pack.acknum}")
                except Exception as e:
                    print(f"[{datetime.now()}] Error in buffering thread: {e}")
            except Exception as e:
                print(f"[{datetime.now()}] Error in buffering thread: {e}")
        print(f"[{datetime.now()}] Buffering thread finished")
        self.udp_socket.close()
        exit(0)

    def buffering_thread_client(self):
        """
             this function should run as a thread
             Receive data from server and deliver it to the connection (demultiplexing operation)

             •
             Check SYN packets received for establishing a new connection and perform the handshake operation if valid or not

             And finally, accept them into the queue after success

             Identify invalid packets or packets from unknown connections, and ignore or respond appropriately (e.g., RST packet) to them.
             """
        print(f"[{datetime.now()}] Buffering thread started on {self.src_ip}:{self.src_port}")
        while not self.is_closed and self.is_client:
            try:
                if self.connection_client.is_closed:
                    self.is_closed = True
                    self.udp_socket.close()
                    print(f"[{datetime.now()}] Client buffering thread stopped: connection closed")
                    exit()
                self.udp_socket.settimeout(10)
                recv_bytes, addr = self.udp_socket.recvfrom(1024)
                pack = None
                try:
                    pack = packet.from_bytes(recv_bytes)
                    print(f"[{datetime.now()}] Received packet from {addr} | Seq: {pack.seqnum} | Ack: {pack.acknum} | Flags: {pack.flag} | Payload size: {len(pack.payload)}")
                    if addr == (self.connection_client.target_ip, self.connection_client.target_port) and self.is_client:
                        if pack.is_ack():
                            self.connection_client.add_to_ack(pack)
                            print(f"[{datetime.now()}] Forwarded ACK packet to client connection")
                        elif pack.is_fin():
                            print(f"[{datetime.now()}] Received FIN packet from server")
                            self.connection_client.add_fin(pack)
                        elif pack.is_rst():
                            self.connection_client.is_closed = True
                            self.connection_client.dispatcher.turn_off()
                            print(f"[{datetime.now()}] Connection closed by RST from server")
                            self.is_closed = True
                            self.udp_socket.close()
                            exit()
                        else:
                            self.connection_client.add_packet(pack)
                            print(f"[{datetime.now()}] Forwarded data packet to client connection")
                    else:
                        print(f"[{datetime.now()}] Unknown packet from {addr}")
                except Exception as e:
                    print(f"[{datetime.now()}] Error in buffering thread: {e}")
            except OSError as e:
                print(f"[{datetime.now()}] Buffer : {e}")
                global counter
                counter += 1
                if counter >= 5:
                    self.close()
                    print(f"[{datetime.now()}] Socket client closed: {e}")

# from datetime import datetime
# import queue
# import socket
# import threading
# import random
# from logging import exception
# from time import sleep
#
# from TOUSendDisptcher import TOUSendDispatcher as Dispatcher
# from TOUConnection import TOUConnection as Connection
# from TOUPacket import TOUPacket as packet
# #flag = {'SYN':False,'ACK':False,'RST':False,'FIN':False}
# MTU = 1500
# Num_packet =0
# counter = 0
# class TOUSocket:
#     src_ip :str = ''
#     src_port :int = 0
#     can_work = True
#     remote_addr :str = ''
#     remote_port :int = 0
#     udp_socket :socket.socket = None
#     accept_queue :queue.Queue = queue.Queue()
#     connection_dict = dict[(str,int),(Connection,bool)]
#     server_port :int = 0
#     ack_dict = dict[(str,int),int]
#     is_closed :bool = False
#     is_server :bool = False
#     is_client :bool = False
#     mss : int  =1024
#     dispacher:Dispatcher = None
#
#     closing = False
#     connection_client: Connection
#
#
#     def __init__(self) -> None:
#         self.closing = None
#         self.ack_dict = {}
#         self.connection_dict = {}
#
#     def generate_seq(self):
#         a =  random.randint(0, 2 ** 20 - 1)
#
#         while a in self.ack_dict.values():
#             a = random.randint(0, 2 ** 32 - 1)
#         return a
#
#
#     def socket(self,mss = 1024):
#         self.mss = mss
#         self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     def bind(self,ipaddr,port):
#        """
#        bind  ipaddress and port on TOPSocket
#
#        """
#        if self.udp_socket is not None:
#         print(f"{ipaddr}:{port} is binding...")
#         self.udp_socket.bind((ipaddr,port))
#         self.src_ip = ipaddr
#         self.src_port = port
#        else:
#            raise Exception('udp socket not initialized')
#
#
#     def listen(self,accept_queue_size = 3):
#         """
#         listen on a socket to make a connection
#
#         :param accept_queue_size: maximum number of  connections want to accept
#         """
#         if  not self.is_client:
#             self.is_server = True
#             self.accept_queue = queue.Queue(accept_queue_size)
#             self.dispacher = Dispatcher(self.udp_socket)
#             t = threading.Thread(target=self.buffering_thread_server,args=() , name ='buffering_thread_server')
#             t.start()
#
#
#     def accept(self):
#             """
#             accept connection and make a TOP connection
#             :returns: TOPConnection , ipaddr and port
#             """
#             try :
#                 conn,addr = self.accept_queue.get(timeout=10)
#                 self.connection_dict[addr] = (conn,True)
#                 return conn,addr
#             except queue.Empty:
#                 raise Exception('No connection Founded.')
#
#     def connect(self,ipaddr,port,window_size=4096,mss=1024):
#         if self.is_server :
#             raise exception("This is a client_method but your socket is server.")
#         self.is_client = True
#         try:
#             self.udp_socket.getsockname()
#         except socket.error:
#             self.udp_socket.bind(('0.0.0.0', 0))
#         self.src_ip ,self.src_port = self.udp_socket.getsockname()
#         randseq = self.generate_seq()
#         syn_packet =packet(self.src_port,
#                            port,
#                             randseq,
#                             0,
#                             {'SYN':True,'ACK':False
#                                 ,'RST':False,'FIN':False}
#                                 ,window_size
#                                 ,mss=mss)
#         self.udp_socket.sendto(syn_packet.to_bytes(),(ipaddr,port))
#         try :
#             rwnd =0
#             self.udp_socket.settimeout(10)
#             recv_byte =self.udp_socket.recvfrom(MTU)
#             pack = packet.from_bytes(recv_byte)
#
#             ack_packet = None
#             if pack.acknum == randseq+1 :
#                 rwnd = pack.window_size
#                 ack_packet = packet(self.src_port,
#                                     port,
#                                     randseq+1,
#                                     pack.seqnum,
#                                     {'SYN': False, 'ACK': True
#                                         , 'RST': False, 'FIN': False}
#                                     , window_size
#                                     , mss=mss)
#             self.udp_socket.sendto(ack_packet.to_bytes(),(ipaddr,port))
#             self.connection_client = Connection(self.udp_socket,self.src_ip,self.src_port
#                                                 ,ipaddr,port,rwnd,pack.acknum,pack.seqnum,window_size,mss=mss)
#             t = threading.Thread(target=self.buffering_thread_client, args=(), name ='buffering_thread_client')
#             t.start()
#
#             print(f"[{datetime.now()}] Client connect to {ipaddr}:{port}.")
#         except socket.timeout as e :
#             print(f"[{datetime.now()}] Connection timed out Server didn't response.")
#             raise exception("Socket timed out.")
#         except exception as e :
#             print(f"[{datetime.now()}] Error occured {e}.")
#             self.is_client = False
#             raise exception(f"an undefined error occured. {e}")
#
#     def send(self,array: bytearray):
#         if self.is_client :
#             self.connection_client.send(array)
#
#     def receive (self ,length:int):
#         if self.is_client:
#             data = self.connection_client.receive(length)
#             return data
#
#
#     def close(self):
#         if self.is_server:
#             print(f'[{datetime.now()}] Server is closing...')
#             self.can_work = False
#             for conn,status in self.connection_dict.values():
#                 if not status:
#                     conn.close_by_rst()
#         elif self.is_client:
#             print(f'[{datetime.now()}] Client is closing...')
#             self.connection_client.close()
#
#     def send_rst_packet(self, addr: tuple):
#         """
#         Send a TCP Reset (RST) packet to the target.
#         This should be used to abort a connection.
#
#         :param addr : address to send the Rst packet to
#         """
#         rst_pkt = packet(
#             self.src_port,
#             addr[1],
#             0,
#             0,
#             {'SYN': False, 'ACK': False, 'RST': True, 'FIN': False},
#             window_size=10,
#             mss=self.mss,
#             payload=bytearray()
#         )
#         try:
#             self.udp_socket.sendto(rst_pkt.to_bytes(), (addr[0], addr[1]))
#             print(f"[{datetime.now()}] Sent RST packet: Address: {addr}")
#         except Exception as e:
#             print(f"[{datetime.now()}] Error sending RST packet: {e}")
#
#
#     def buffering_thread_server(self):
#         """
#         this function should run as a thread
#         Receive data from active connections and deliver it to the corresponding connections (demultiplexing operation)
#
#         •
#         Check SYN packets received for establishing a new connection and perform the handshake operation if valid or not
#
#         And finally, accept them into the queue after success
#
#         Identify invalid packets or packets from unknown connections, and ignore or respond appropriately (e.g., RST packet) to them.
#          """
#         print(f"[{datetime.now()}] Buffering thread started on {self.src_ip}:{self.src_port} ")
#         while not self.is_closed:
#
#             dellist = []
#             for conn in self.connection_dict.keys():
#
#                 if self.connection_dict[conn][0].is_closed :
#                     dellist.append(conn)
#             for conn in dellist:
#                 self.connection_dict.pop(conn,None)
#                 self.dispacher.delete_packet_conn(conn)
#             try:
#
#                     self.udp_socket.settimeout(10)
#                     recv_bytes, addr= self.udp_socket.recvfrom(1024)
#                     pack = None
#                     try:
#                         if not self.can_work and len(self.connection_dict) == 0:
#                             self.is_closed = True
#                             self.dispacher.turn_off()
#                         pack = packet.from_bytes(recv_bytes)
#                         randseq = self.generate_seq()
#                         print(
#                             f"{datetime.now()}: get packet :address:{addr}: "
#                             f"seqnum :{pack.seqnum}: acknum : {pack.acknum}: payload : {pack.payload}")
#
#                         #if client want to establish a connection
#                         if pack.is_sync() and not pack.is_ack() and not pack.is_fin() and not pack.is_rst() and self.can_work:
#                             # if addr in self.connection_dict.keys():
#                                 ack_apk = packet(pack.dest_port,
#                                         pack.source_port,
#                                         randseq,
#                                         pack.seqnum+1,
#                                     {'SYN':True,'ACK':True
#                                         ,'RST':False,'FIN':False}
#                                         ,pack.window_size,mss=pack.mss)
#                                 self.ack_dict[addr] = randseq
#                                 self.dispacher.write(ack_apk, addr)
#
#
#                        # establish connection and add client to accept list
#                         elif addr in self.ack_dict.keys() and self.can_work:
#                             if pack.is_ack() and not pack.is_fin() and not pack.is_rst() and not pack.is_sync():
#                                 if pack.acknum ==(self.ack_dict[addr]) :
#                                     conn = Connection(self.udp_socket
#                                                       , self.src_ip
#                                                       , self.src_port
#                                                       , addr[0]
#                                                       , addr[1]
#                                                       , pack.window_size
#                                                       , pack.acknum
#                                                       , pack.seqnum
#                                                       )
#                                     self.connection_dict[addr] = (conn,False)
#                                     self.accept_queue.put((conn, addr))
#                                     print(f"[{datetime.now()}] Connection accepted {addr}.")
#                                     self.ack_dict.pop(addr)
#
#
#
#                         # send packet to appropriate connection.
#                         elif addr in self.connection_dict.keys() :
#                             if pack.is_ack():
#                                 self.connection_dict[addr][0].add_to_ack(pack)
#                             elif pack.is_fin():
#                                 self.connection_dict[addr][0].add_fin(pack)
#                             elif pack.is_rst():
#                                 self.connection_dict[addr][0].is_closed = True
#                                 self.connection_dict[addr][0].dispatcher.turn_off()
#                                 print(f"[{datetime.now()}] Connection closed By RST flag.")
#
#                             else:
#                                 self.connection_dict[addr][0].add_packet(pack)
#                             ### DROP PACKET
#                             # global Num_packet
#                             # Num_packet += 1
#                             # if Num_packet == 5:
#                             #     print(f"[{datetime.now()}] Packet Droped {pack}")
#                             # else:
#                             #     self.connection_dict[addr][0].add_packet(pack)
#
#                         else:
#                             print(f"[{datetime.now()}] unknown packet found {pack} From {addr}.")
#
#                     except Exception as e:
#                         print(f"[Error] Error in buffering thread as {e}")
#                     except OSError as e:
#                         print(f"[Warning] Socket server is closed {e}")
#             except Exception as e:
#                 print(f"[Error] Error in buffering thread as {e}")
#         print(f"{datetime.now()} Buffering thread finished!")
#         self.udp_socket.close()
#         exit(0)
#
#
#
#     def buffering_thread_client(self):
#         """
#             this function should run as a thread
#             Receive data from server and deliver it to the connection (demultiplexing operation)
#
#             •
#             Check SYN packets received for establishing a new connection and perform the handshake operation if valid or not
#
#             And finally, accept them into the queue after success
#
#             Identify invalid packets or packets from unknown connections, and ignore or respond appropriately (e.g., RST packet) to them.
#              """
#         print(f"[{datetime.now()}] Buffering thread started on {self.src_ip}:{self.src_port} ")
#         while not self.is_closed and self.is_client:
#             try:
#                     if self.connection_client.is_closed :
#                         is_closed = True
#                         self.udp_socket.close()
#                         exit()
#                     self.udp_socket.settimeout(10)
#                     recv_bytes, addr = self.udp_socket.recvfrom(1024)
#                     pack = None
#                     try:
#                         pack = packet.from_bytes(recv_bytes)
#                         print(
#                             f"{datetime.now()}: get packet :address:{addr}: "
#                             f"seqnum :{pack.seqnum}: acknum : {pack.acknum}: payload : {pack.payload}")
#
#                         # send packet to appropriate connection.
#                         if addr == (self.connection_client.target_ip, self.connection_client.target_port) and self.is_client:
#                             if pack.is_ack():
#                                 self.connection_client.add_to_ack(pack)
#                             elif pack.is_fin():
#                                 print(f"[{datetime.now()} Get Fin Packet")
#                                 self.connection_client.add_fin(pack)
#                             elif pack.is_rst():
#                                 self.connection_client.is_closed = True
#                                 self.connection_client.dispatcher.turn_off()
#                                 print(f"[{datetime.now()}] Connection closed By RST flag.")
#                                 self.is_closed = True
#                                 self.udp_socket.close()
#                                 exit()
#                             else:
#                                 self.connection_client.add_packet(pack)
#                         else:
#                             print(f"[{datetime.now()}] unknown packet found {pack}")
#                     except Exception as e:
#                         print(f"[Error] Error in buffering thread as {e}")
#             except OSError as e :
#                 print(f"[Warning] Socket client is closed {e}")
#                 global counter
#                 counter +=1
#                 if counter >= 5:
#                     self.close()
#
