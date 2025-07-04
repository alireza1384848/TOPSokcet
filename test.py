import queue

bu = queue.Queue()
bu.put(1)
bu.put(2)


print (bu.qsize())


buffer = bytearray()

buffer += b'10001'
buffer += b'0001'
buffer += b'10000'


print(buffer)
