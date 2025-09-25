# TOU Protocol Implementation

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-In%20Development-orange.svg)

## Introduction

**TOU** (Transport Over UDP) is a custom transport protocol implemented in Python, designed to provide reliable data transfer over UDP, inspired by TCP's reliability features. This project includes a socket-like interface (`TOUSocket`), connection management (`TOUConnection`), and packet dispatching (`TOUSendDispatcher`) to handle reliable communication, including sequence numbers, acknowledgments, and connection state management.

This project serves as an educational tool for understanding low-level networking concepts and protocol design. It is ideal for students, network programming enthusiasts, or developers interested in custom protocol implementation.

## Features

- **Reliable Data Transfer**: Ensures data delivery using sequence and acknowledgment numbers.
- **Connection Management**: Supports connection establishment, data transfer, and graceful termination (FIN/RST).
- **Zero Window Handling**: Manages flow control with window size and probing mechanisms.
- **Error Handling**: Robust handling of timeouts, retransmissions, and connection resets.
- **Modular Design**: Separates concerns into socket, connection, and dispatcher modules for maintainability.
- **Detailed Logging**: Comprehensive logs for debugging and tracking packet flow.

## Installation

### Prerequisites
- Python 3.8 or higher
- No external libraries required (uses standard Python libraries: `socket`, `queue`, `threading`, etc.)

### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/alireza1384848/TOPSokcet.git
   cd tou-protocol
   ```

2. Verify Python installation:
   ```bash
   python --version
   ```

3. (Optional) Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

## Usage

### Running the Server
1. Start the server using `TOUSocket.py`:
   ```bash
   python TOUSocket.py
   ```
2. The server binds to a specified IP and port (e.g., `127.0.0.1:5000`) and listens for incoming connections.

### Running the Client
1. Connect to the server using `TOUSocket.py` in client mode:
   ```bash
   python TOUSocket.py --client <server_ip> <server_port>
   ```
   Example:
   ```bash
   python TOUSocket.py --client 127.0.0.1 5000
   ```

2. Send and receive data using the `send` and `receive` methods of the `TOUSocket` class.

### Example
```python
from TOUSocket import TOUSocket

# Server
server = TOUSocket()
server.socket(mss=1024)
server.bind("127.0.0.1", 5000)
server.listen()
conn, addr = server.accept()
conn.send(b"Hello, Client!")
data = conn.receive(1024)
print(f"Received: {data}")
server.close()

# Client
client = TOUSocket()
client.socket(mss=1024)
client.connect("127.0.0.1", 5000, window_size=4096)
client.send(b"Hello, Server!")
data = client.receive(1024)
print(f"Received: {data}")
client.close()
```

## Project Structure

- **`TOUSocket.py`**: Implements the main socket interface for client and server operations.
- **`TOUConnection.py`**: Manages connection state, data transfer, and flow control.
- **`TOUSendDispatcher.py`**: Handles packet queuing and sending over UDP.
- **`TOUPacket.py`**: Defines the packet structure and serialization for the TOU protocol.

## Logging

The project includes detailed logging to track:
- Packet sending/receiving with sequence numbers, acknowledgment numbers, and payload sizes.
- Connection states (e.g., establishment, closure, Zero Window).
- Errors and retransmissions for debugging purposes.

Example log output:
```
[2025-07-12 12:26:00.123456] Connection initialized: 127.0.0.1:5000 -> 127.0.0.1:6000 | Seq: 12345 | Ack: 0
[2025-07-12 12:26:00.125000] Sent packet to (127.0.0.1, 6000) | Seq: 12345 | Ack: 0 | Flags: {'SYN': True, 'ACK': False, 'RST': False, 'FIN': False} | Payload size: 0
```

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository.
2. Create a new branch: `git checkout -b feature/your-feature`.
3. Make your changes and commit: `git commit -m "Add your feature"`.
4. Push to your branch: `git push origin feature/your-feature`.
5. Open a pull request.



## Acknowledgments

- Inspired by TCP protocol design and network programming concepts.
- Thanks to the Python community for excellent documentation and standard libraries.

## Contact

For questions or feedback, feel free to open an issue or contact me at [your-email@example.com](mailto:your-email@example.com).

---

Happy coding! 🚀
