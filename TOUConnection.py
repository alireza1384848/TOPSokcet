from datetime import datetime
from logging import exception
from queue import  Queue
import threading
import random
from typing import Union
from socket import socket

from Tools.scripts.md5sum import bufsize

#import TOUSocket
from TOUPacket import TOUPacket as packet


class TOUConnection:
    source_ip:str = ''
    source_port:int = 0
    target_ip:str = ''
    target_port:int = 0
    socket:socket = None
    BUFFER_SIZE : int = 50000
    mss : int = 0
    window_size : int = 0


    SEND_BUFFER = bytearray(BUFFER_SIZE)
    SEND_BUFFER_BASE: int =0
    NEXT_SEQ_NUM_SEND: int =0
    LAST_DATA_SEND : int =0

    RECV_BUFFER = bytearray(BUFFER_SIZE)
    RECV_BUFFER_BASE: int = 0
    READY_READ_POS_RECV: int =0
    NEXT_SEQ_NUM_RECV: int = 0
    LAST_DATA_RECV: int = 0

    is_closed:bool = False
    def __init__(self,sock:socket,source_ip:str, source_port:int, target_ip:str, target_port:int,window_size :int=50000,buffer_size :int= 50000, mss:int=1024):
        self.source_ip = source_ip
        self.source_port = source_port
        self.target_ip = target_ip
        self.target_port = target_port
        self.BUFFER_SIZE = buffer_size
        self.socket = sock
        self.mss = mss
        self.window_size = window_size

    def write_to_receive_buffer(self ,bytearr: bytearray) :
        if self.BUFFER_SIZE - self.LAST_DATA_SEND > len(bytearr):
            self.SEND_BUFFER[self.LAST_DATA_SEND+1: self.LAST_DATA_SEND+len(bytearr)+1] = bytearr
            return len(bytearr)
        else :
            return 0

    def send(self,array: bytearray):
        if not self.is_closed:
            while self.BUFFER_SIZE - self.LAST_DATA_SEND < len(array):
                pass
            self.SEND_BUFFER[self.LAST_DATA_SEND+1: self.LAST_DATA_SEND+len(array)+1] = array


    def receive (self ,length:int) -> Union[int, bytearray, None]:
        if not self.is_closed:
            while  self.READY_READ_POS_RECV - self.RECV_BUFFER_BASE < length :
                pass
            data = self.RECV_BUFFER[self.RECV_BUFFER_BASE:self.RECV_BUFFER_BASE+length+1]
            self.RECV_BUFFER = self.RECV_BUFFER[self.RECV_BUFFER_BASE+length+1:] + bytearray(length)
            return data

    def close(self):
        randseq = random.randint(0, 2 ** 32 - 1)
        randack = random.randint(0, 2 ** 32 - 1)
        pac :packet = packet(self.source_port,
                           self.target_port,
                           randseq,
                            randack,
                            {'SYN': False, 'ACK': False
                            , 'RST': False, 'FIN': True},
                            100,
                            self.mss
                           )
        socket.sendto(pac.to_bytes(),(self.target_ip,self.target_port))
        try:
            #  TODO: change this when you write thread's
            pack = socket.recvfrom(1024)
            pack = packet.from_bytes(pack)
            if pack.is_ack() and pack.seqnum == randack:
                print(f"[{datetime.now()}] Connection closed from {self.source_ip}:{self.source_port}.")
                self.is_closed = True

        except exception as e:
            pass
        except socket.timeout:
            pass



