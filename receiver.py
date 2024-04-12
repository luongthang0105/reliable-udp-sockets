#!/usr/bin/env python3
# -*- coding: utf-8 -*-

###
# Main Modifications
# ==================
# Command line arguments: now include my_port, peer_port (the other side's port).
# Bind and connect: use bind((('127.0.0.1', my_port)) to bind to own port and connect(('127.0.0.1', peer_port)) to a specific sender.
# Data Receiving and Sending: Receive data via recv() and send a response using send() without specifying the other party's address and port.
# Changes to the log output.
###

import socket
import sys
from arg_parser import ArgParser
from helpers import Helpers
from enums import LogActions, SegmentType

NUM_ARGS = 4  # Number of command-line arguments
BUF_SIZE = 1004  # Size of buffer for sending/receiving data

if __name__ == "__main__":
    if len(sys.argv) != NUM_ARGS + 1:
        sys.exit(f"Usage: {sys.argv[0]} rcvr_port sender_port txt_file_received max_win")

    # ================== Update arguments =====================
    rcvr_port = ArgParser.parse_port(sys.argv[1]) 
    sender_port = ArgParser.parse_port(sys.argv[2])
    txt_file_received = sys.argv[3]
    max_win = ArgParser.parse_max_win(sys.argv[4])

    # ================== Update socket setup =====================
    Helpers.reset_log('receiver')
    
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(('127.0.0.1', rcvr_port))
        s.connect(('127.0.0.1', sender_port))

        while True:
            receive = s.recv(BUF_SIZE)
            segmentType = int.from_bytes(receive[:2], 'big')

            if segmentType == SegmentType.SYN:
                seqno = int.from_bytes(receive[2:4], 'big')
                # For SYN segment, add 1 to seqno
                seqno += 1
    sys.exit(0)