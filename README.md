# Reliable UDP Sockets (Simple Transport Protocol - STP)

## Overview  
This project implements a simplified transport protocol (STP) for reliable, uni-directional file transfer over UDP using Python. The protocol mimics key TCP features, including connection setup, data transmission, acknowledgments, and connection termination. It also includes an unreliable channel simulation, where packet loss can be configured for both forward (data) and reverse (ACK) directions.  

## Features  
- **Stop-and-Wait Protocol:** Implements reliable data transfer with a single outstanding packet at a time.  
- **Sliding Window Protocol:** Supports window-based data transfer to improve efficiency.  
- **Unreliable Channel Simulation:** Allows packet loss in both directions, controlled via command-line parameters. This is to simulate the real-world network traffic, where packet drops are somewhat random.
- **Logging:** Generates detailed sender and receiver logs to track packet transmission, reception, and loss.

## Usage  
### Receiver  
```sh
python receiver.py <receiver_port> <sender_port> <txt_file_received> <max_win>
```  
### Sender  
```sh
python sender.py <sender_port> <receiver_port> <txt_file_to_send> <max_win> <rto> <flp> <rlp>
```  
### Parameters  
- `max_win`: Window size for the sliding window protocol (multiple of MSS = 1000 bytes).  
- `rto`: Retransmission timeout in milliseconds.  
- `flp`: Forward loss probability (0 to 1).  
- `rlp`: Reverse loss probability (0 to 1).  

## Implementation Details  
- **Sender**: Manages file transmission, retransmissions, and packet loss simulation.  
- **Receiver**: Handles segment reception, ACK generation, and buffering for out-of-order segments.  
- **State Machine**: Implements TCP-like state transitions for reliable communication.  
- **Threading**: Uses multiple threads or non-blocking I/O for handling concurrent events.  

## Logs  
- **sender_log.txt**: Tracks sent, received, and dropped packets.  
- **receiver_log.txt**: Logs received packets and acknowledgments.  

## Testing  
- Run both sender and receiver on the same machine using `localhost`.  
- Test with different values of `flp` and `rlp` to evaluate performance under packet loss conditions.  
