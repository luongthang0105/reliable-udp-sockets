#!/usr/bin/env python3
# -*- coding: utf-8 -*-

###
# Main Modifications
# ==================
# Command line parameter changes: my_port and rcvr_port, which specifies both the sender's port and the receiver's port.
# Adjustments to the setup_socket function: updated this function so that it binds not only to the sender's port (my_port), but also connects to the receiver's address and port (rcvr_port) via connect.
# Changes to the log output.
###

import random
import socket
import sys
import threading
from dataclasses import dataclass
from arg_parser import ArgParser
from helpers import Helpers
from states import States
from stp_helpers import Stp

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
    seqno_map: dict     # A dictionary to map seqno to its corresponding index in list
    dupACK_cnt: int = 0 # The count of duplicate ACKed segment for fast retransmit 

# =====================Update setup_socket function ========================
def setup_socket(sender_port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # bind to sender port
    sock.bind(('127.0.0.1', sender_port))
    return sock

if __name__ == "__main__":
    if len(sys.argv) != NUM_ARGS + 1:
        sys.exit(f"Usage: {sys.argv[0]} sender_port rcvr_port txt_file_to_send max_win rto flp rlp")

    sender_port   = ArgParser.parse_port(sys.argv[1])
    rcvr_port = ArgParser.parse_port(sys.argv[2])
    txt_file_to_send = ArgParser.parse_file_name(sys.argv[3])
    max_win = ArgParser.parse_max_win(sys.argv[4])
    rto = ArgParser.parse_rto(sys.argv[5])
    flp = ArgParser.parse_prop(sys.argv[6])
    rlp = ArgParser.parse_prop(sys.argv[7])

    Helpers.reset_log('sender')

    sock = setup_socket(sender_port)

    # Use a fixed seed for debugging purpose, NEED TO CHANGED BEFORE SUBMITTED
    random.seed(1)  # Seed the random number generator
    isn = random.randrange(MAX_SEQNO)

    # Create a control block for the sender program.
    control = Control(sender_port=sender_port, rcvr_port=rcvr_port, 
                      socket=sock, max_win=max_win, seqno=isn, rto=rto,
                      file_name=txt_file_to_send, flp=flp, rlp=rlp)
    States.state_syn_sent(control)
    print('Finished 2-way Connection Setup')

    States.state_est(control)

    control.socket.close()  # Close the socket

    print("Shut down complete.")

    sys.exit(0)
