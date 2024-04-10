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

NUM_ARGS = 3  # Number of command-line arguments
BUF_SIZE = 3  # Size of buffer for sending/receiving data

if __name__ == "__main__":
    if len(sys.argv) != NUM_ARGS + 1:
        sys.exit(f"Usage: {sys.argv[0]} rcvr_port sender_port txt_file_received max_win")

    # ================== Upasdasdasdate arguments =====================
    rcvr_port = ArgParser.parse_port(sys.argv[1]) 
    sender_port = ArgParser.parse_port(sys.argv[2])
    txt_file_received = sys.argv[3]
    max_win = ArgParser.parse_max_win(sys.argv[4])

    # ================== Update socket setup =====================
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(('127.0.0.1', my_port)) 
        s.connect(('127.0.0.1', peer_port))
        s.settimeout(wait_time)

        while True:
            # Here we're using recvfrom() and sendto(), but we could also 
            # connect() this UDP socket to set communication with a particular 
            # peer. This would allow us to use send() and recv() instead, 
            # but only communicate with one peer at a time.
            # ====================== Update to send() and recv() ================
            try:
                buf = s.recv(BUF_SIZE)
            except socket.timeout:
                print(f"No data within {wait_time} seconds, shutting down.")
                break

            if len(buf) < BUF_SIZE-1:
                print(f"recvfrom: received short message: {buf}", file=sys.stderr)
                continue

            # Packet was received, first (and only) field is multi-byte, 
            # so need to convert from network byte order (big-endian) to 
            # host byte order.  Then log the recv.
            num = int.from_bytes(buf[:2], byteorder='big')
            print(f"127.0.0.1:{peer_port}: rcv: {num:>5}")

            # Determine whether the number is odd or even, and append the 
            # result (as a single byte) to the buffer.
            odd = num % 2
            buf += odd.to_bytes(1, byteorder='big')

            # Log the send and send the reply.
            print(f"127.0.0.1:{peer_port}: snd: {num:>5} {'odd' if odd else 'even'}")
            if (s.send(buf) != len(buf)):
                print(f"sendto: partial/failed send, message: {buf}", file=sys.stderr)
                continue

    sys.exit(0)