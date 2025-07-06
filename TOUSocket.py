from datetime import datetime
import queue
import socket
import threading
import random
from logging import exception

from TOUConnection import TOUConnection as Connection
from TOUPacket import TOUPacket as packet
#flag = {'SYN':False,'ACK':False,'RST':False,'FIN':False}

class TOUSocket:
    src_ip :str = ''
    src_port :int = 0
    remote_addr :str = ''
    remote_port :int = 0
    udp_socket :socket.socket = None
    accept_queue :queue.Queue = queue.Queue()
    connection_dict = dict[(str,int),Connection]
    server_port :int = 0
    ack_dict = dict[(str,int),int]
    is_closed :bool = False
    is_server :bool = False
    is_client :bool = False
    mss : int  =1024

    server_ip :str = ''
    server_port :int = 0


    def __init__(self) -> None:
        self.ack_dict = {}
        self.connection_dict = {}

    def generate_seq(self):
        a =  random.randint(0, 2 ** 32 - 1)
        print(len(self.ack_dict))
            # while a in self.ack_dict.values:
            #     a = random.randint(0, 2 ** 32 - 1)
        return a


    def socket(self,mss = 1024):
        self.mss = mss
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    def bind(self,ipaddr,port):
       """
       bind  ipaddress and port on TOPSocket

       """
       if self.udp_socket is not None:
        print(f"{ipaddr}:{port} is binding...")
        self.udp_socket.bind((ipaddr,port))
        self.src_ip = ipaddr
        self.src_port = port
       else:
           raise Exception('udp socket not initialized')


    def listen(self,accept_queue_size = 3):
        """
        listen on a socket to make a connection

        :param accept_queue_size: maximum number of  connections want to accept
        """
        if  not self.is_client:
            self.is_server = True
            self.accept_queue = queue.Queue(accept_queue_size)
            t = threading.Thread(target=self.buffering_thread,args=())
            t.start()


    def accept(self):
            """
            accept connection and make a TOP connection
            :returns: TOPConnection , ipaddr and port
            """
            addr : (str,int)= self.accept_queue.get()
            conn = Connection(self.udp_socket
                              , addr[0]
                              , addr[1]
                              , self.src_ip
                              , self.src_port)
            self.connection_dict[addr] = conn

            return conn,addr

    def connect(self,ipaddr,port,window_size=5000,mss=1024):
        if self.is_server :
            raise exception("This is a client_method but your socket is server.")
        self.is_client = True
        try:
            self.udp_socket.getsockname()
        except socket.error:
            self.udp_socket.bind(('0.0.0.0', 0))
        self.src_ip ,self.src_port = self.udp_socket.getsockname()
        randseq = self.generate_seq()
        syn_packet =packet(self.src_port,
                           port,
                            randseq,
                            0,
                            {'SYN':True,'ACK':False
                                ,'RST':False,'FIN':False}
                                ,window_size
                                ,mss=mss)
        self.udp_socket.sendto(syn_packet.to_bytes(),(ipaddr,port))
        try :
            self.udp_socket.settimeout(5)
            recv_byte =self.udp_socket.recvfrom(mss)
            pack = packet.from_bytes(recv_byte)
            #todo : check this condition\
            ack_packet = None
            if pack.acknum == randseq+1 :
                ack_packet = packet(self.src_port,
                                    port,
                                    randseq+1,
                                    pack.seqnum,
                                    {'SYN': False, 'ACK': True
                                        , 'RST': False, 'FIN': False}
                                    , window_size
                                    , mss=mss)
            self.udp_socket.settimeout(10000)
            self.udp_socket.sendto(ack_packet.to_bytes(),(ipaddr,port))
            self.server_ip = ipaddr
            self.server_port = port
            print(f"[{datetime.now()}] Client connect to {ipaddr}:{port}.")
        except socket.timeout as e :
            print(f"[{datetime.now()}] Connection timed out Server didn't response.")
            raise exception("Socket timed out.")
        except exception as e :
            print(f"[{datetime.now()}] Error occured {e}.")
            self.is_client = False
            raise exception(f"an undefined error occured. {e}")

    def buffering_thread(self):
        """
        this function should run as a thread
        Receive data from active connections and deliver it to the corresponding connections (demultiplexing operation)

        •
        Check SYN packets received for establishing a new connection and perform the handshake operation if valid or not

        And finally, accept them into the queue after success

        Identify invalid packets or packets from unknown connections, and ignore or respond appropriately (e.g., RST packet) to them.
         """
        print(f"[{datetime.now()}] Buffering thread started on {self.src_ip}:{self.src_port} ")
        while not self.is_closed:
            for conn in self.connection_dict.values():
                if conn.is_closed :self.connection_dict.pop(conn)
            print(self.connection_dict.keys())
            self.udp_socket.settimeout(1000)
            recv_bytes, addr= self.udp_socket.recvfrom(1024)
            pack = None
            try:
                print(recv_bytes)
                pack = packet.from_bytes(recv_bytes)
                randseq = self.generate_seq()
                #if client want to establish a connection
                if pack.is_sync() and not pack.is_ack() and not pack.is_fin() and not pack.is_rst():
                    ack_apk = packet(pack.dest_port,
                                pack.source_port,
                                randseq,
                                pack.seqnum+1,
                            {'SYN':True,'ACK':True
                                ,'RST':False,'FIN':False}
                                ,pack.window_size,mss=pack.mss)
                    self.ack_dict[addr] = randseq
                    self.udp_socket.sendto(ack_apk.to_bytes(), addr)
               # establish connection and add client to accept list
                elif addr in self.ack_dict.keys() :
                    if pack.is_ack() and not pack.is_fin() and not pack.is_rst() and not pack.is_sync():
                        if pack.acknum ==(self.ack_dict[addr]) :
                            self.accept_queue.put(addr)
                            print(f"[{datetime.now()}] Connection accepted {addr}.")
                # send packet to appropriate connection.
                elif addr in self.connection_dict.keys():
                    self.connection_dict[addr].write_to_receive_buffer(pack.payload)
                else:
                    print(f"[{datetime.now()}] unknown packet found {pack}")

            except Exception as e:
                print(f"[Error] Error in buffering thread as {e}")


