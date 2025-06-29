import struct
from builtins import bytes

class TOUPacket:
    source_port :int= 0
    dest_port :int = 0
    seqnum :int = 0
    acknum :int = 0
    flag = {'SYN':False,'ACK':False,'RST':False,'FIN':False}
    window_size :int = 0
    payload :bytes = bytes(1)
    payload_len :int = 0
    mss :int = 0
    def __init__(self,s_port,d_port,seqnum,acknum,flag,window_size,payload = b'',mss=1024):
        self.source_port = s_port
        self.dest_port = d_port
        self.seqnum = seqnum
        self.acknum = acknum
        self.flag = flag
        self.window_size = window_size
        self.payload = payload
        self.payload_len = len(payload)
        self.mss = mss

    def to_bytes(self):
        flag_bytes = (
        (self.flag.get('SYN',False) << 3)|
        (self.flag.get('ACK',False)<<2)|
        (self.flag.get('RST',False)<<1)|
        (self.flag.get('FIN',False)<<0)
        )
        header = (struct.pack
                  ('!HHIIBHHI',
                   self.source_port,
                   self.dest_port,
                   self.seqnum,
                   self.acknum,
                   flag_bytes,
                   self.window_size,
                   self.payload_len,
                   self.mss,))
        return header + self.payload



    @classmethod
    def from_bytes(cls, data) :
        header_size = struct.calcsize('!HHIIBHHI')
        header = data[:header_size]
        payload = data[header_size:]

        src_port, dst_port, seq_num, ack_num, flags_byte, window, payload_len,mss = struct.unpack('!HHIIBHH', header)

        flags = {
            'SYN': bool(flags_byte & 0b1000),
            'ACK': bool(flags_byte & 0b0100),
            'FIN': bool(flags_byte & 0b0010),
            'RST': bool(flags_byte & 0b0001),
        }

        return cls(
            src_port,
            dst_port,
            seq_num,
            ack_num,
            flags,
            window,
            payload[:payload_len],
            mss
        )
    def is_sync(self):
        return (self.flag['SYN'])

    def is_ack(self):
        return self.flag['ACK']
    def is_rst(self):
        return self.flag['RST']
    def is_fin(self):
        return self.flag['FIN']