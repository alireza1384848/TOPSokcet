from queue import  Queue
import threading
import TOPSocket

class TOPConnection:
    source_ip:str = ''
    source_port:int = 0
    target_ip:str = ''
    target_port:int = 0
    socket:TOPSocket = None
    BUFFER_SIZE : int = 50000

    SEND_BUFFER = bytearray(BUFFER_SIZE)
    SEND_BUFFER_BASE: int =0
    NEXT_SEQ_NUM_SEND: int =0
    LAST_DATA_SEND : int =0

    RECV_BUFFER = bytearray(BUFFER_SIZE)
    RECV_BUFFER_BASE: int = 0
    NEXT_SEQ_NUM_RECV: int = 0
    LAST_DATA_RECV: int = 0

    is_closed:bool = False
    def __init__(self,socket:TOPSocket ,source_ip:str, source_port:int, target_ip:str, target_port:int,buffer_size :int= 50000):
        self.source_ip = source_ip
        self.source_port = source_port
        self.target_ip = target_ip
        self.target_port = target_port
        self.BUFFER_SIZE = buffer_size
        self.socket = socket
    def write_to_receive_buffer(self ,bytearr: bytearray) :
        if self.BUFFER_SIZE - self.LAST_DATA_SEND > len(bytearr):
            self.SEND_BUFFER[self.LAST_DATA_SEND+1: self.LAST_DATA_SEND+len(bytearr)+1] = bytearr
            return len(bytearr)
        else :
            return 0

    def send(self)->bytearray:
        pass


    def receive (self ,bytearr: bytearray):
        pass
