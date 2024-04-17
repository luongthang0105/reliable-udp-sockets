import socket
import threading
from dataclasses import dataclass

NUM_ARGS  = 7  # Number of command-line arguments
BUF_SIZE  = 4  # Size of buffer for receiving messages
MAX_SEQNO = 2**16 # Maximum sequence number
MSS = 1000     # Maximum segment size
@dataclass
class Control:
    """Control block: parameters for the sender program."""
    # ================== Update arguments =====================
    sender_port: int    # Port number of the sender
    rcvr_port: int      # Port number of the receiver
    max_win: int        # max window size, should be the same for receiver side
    rto: float          # retransmission time for a socket
    seqno: int          # sequence number of sender socket
    file_name: str      # name of file being sent
    rlp: float          # probability of incoming packet being dropped
    flp: float          # probability of sent packet being dropped
    socket: socket.socket   # Socket for sending/receiving messages
    is_connected: bool = False # a flag to signal successful connection or when to terminate
    is_est_state: bool = False # a flag to signal whether our sender program is in EST state
    start_time: float = 0.0   # time in miliseconds at first sent segment
    timer: threading.Timer = None # A single timer associates with the EST state

@dataclass 
class SegmentControl:
    """Segment Control block: manages data segments related info"""
    segments: list      # List of 1000 bytes max segments from file
    send_base: int = 0  # The index of the oldest unACKed segment
    end: int = 0        # The end index of current sliding window on segments[]
    seqno_map: dict[int, int] = None # A dictionary to map seqno to its corresponding index in list
    dupACK_cnt: int = 0 # The count of duplicate ACKed segment for fast retransmit 
