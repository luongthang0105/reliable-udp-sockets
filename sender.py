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
from sender_prototypes import NUM_ARGS, MAX_SEQNO, Control

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
    # isn = 0

    # Create a control block for the sender program.
    control = Control(sender_port=sender_port, rcvr_port=rcvr_port, 
                      socket=sock, max_win=max_win, seqno=isn, rto=rto,
                      file_name=txt_file_to_send, flp=flp, rlp=rlp, lock=threading.Lock())
    States.state_syn_sent(control)
    print('Finished 2-way Connection Setup')

    States.state_est(control)
    print('Finished Sending Data Reliably')

    States.state_closing(control)
    control.socket.close()  # Close the socket

    print("Shut down complete.")

    sys.exit(0)
