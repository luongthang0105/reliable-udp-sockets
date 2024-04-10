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
import time
from dataclasses import dataclass
from arg_parser import ArgParser

NUM_ARGS  = 7  # Number of command-line arguments
BUF_SIZE  = 3  # Size of buffer for receiving messages
MAX_SLEEP = 2  # Max seconds to sleep before sending the next message

@dataclass
class Control:
    """Control block: parameters for the sender program."""
    # host: str               # Hostname or IP address of the receiver
    # ================== Update arguments =====================
    my_port: int        # Port number of the sender
    rcvr_port: int      # Port number of the receiver
    socket: socket.socket   # Socket for sending/receiving messages
    max_win: int        # max window size, should be the same for receiver side
    is_connected: bool = False # a flag to signal successful connection or when to terminate


# =====================Update setup_socket function ========================
def setup_socket(sender_port, rcvr_port, timeout=None):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # bind to sender port
    sock.bind(('127.0.0.1', sender_port))
    # connect to peer's address
    sock.connect(('127.0.0.1', rcvr_port))
    if timeout is None:
        sock.setblocking(True)
    else:
        sock.settimeout(timeout)

    return sock

def recv_thread(control):
    """The receiver thread function.

    The recv_thread() function is the entry point for the receiver thread. It
    will sit in a loop, checking for messages from the receiver. When a message 
    is received, the sender will unpack the message and print it to the log. On
    each iteration of the loop, it will check the `is_alive` flag. If the flag
    is false, the thread will terminate. The `is_alive` flag is shared with the
    main thread and the timer thread.

    Args:
        control (Control): The control block for the sender program.
    """
    while control.is_alive:
        try:
            nread = control.socket.recv(BUF_SIZE)
        except BlockingIOError:
            continue    # No data available to read
        except ConnectionRefusedError:
            print(f"recv: connection refused by {control.my_port}:{control.rcvr_port}, shutting down...", file=sys.stderr)
            control.is_alive = False
            break

        if len(nread) < BUF_SIZE - 1:
            print(f"recv: received short message of {nread} bytes", file=sys.stderr)
            continue    # Short message, ignore it

        # Convert first 2 bytes (i.e. the number) from network byte order 
        # (big-endian) to host byte order, and extract the `odd` flag.
        num = int.from_bytes(nread[:2], "big")
        odd = nread[2]

        # Log the received message
        print(f"127.0.0.1:{control.rcvr_port}: rcv: {num:>5} {'odd' if odd else 'even'}")

def timer_thread(control):
    """Stop execution when the timer expires.

    The timer_thread() function will be called when the timer expires. It will
    print a message to the log, and set the `is_alive` flag to False. This will
    signal the receiver thread, and the sender program, to terminate.

    Args:
        control (Control): The control block for the sender program.
    """
    print(f"{control.run_time} second timer expired, shutting down...")
    control.is_alive = False

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


    sock = setup_socket(sender_port, rcvr_port)

    # Create a control block for the sender program.
    control = Control(sender_port, rcvr_port, sock, max_win)

    # Start the receiver and timer threads.
    receiver = threading.Thread(target=recv_thread, args=(control,))
    receiver.start()

    # timer = threading.Timer(run_time, timer_thread, args=(control,))
    # timer.start()

    # Use a fixed seed for debugging purpose, NEED TO CHANGED BEFORE SUBMITTED
    random.seed(1)  # Seed the random number generator
    
    # Send a sequence of random numbers as separate datagrams, until the 
    # timer expires.
    while control.is_alive:
        num = random.randrange(2**16)       # Random number in range [0, 65535]
        net_num = num.to_bytes(2, "big")    # Convert number to network byte order

        # Log the send and then send the random number.
        print(f"127.0.0.1:{rcvr_port}: snd: {num:>5}")
        nsent = control.socket.send(net_num)
        if nsent != len(net_num):
            control.is_alive = False
            sys.exit(f"send: partial/failed send of {nsent} bytes")

        # Sleep for a random amount of time before sending the next message.
        # This is ONLY done for the sake of the demonstration, it should be 
        # removed to maximise the efficiency of the sender.
        time.sleep(random.uniform(0, MAX_SLEEP + 1))
    
    # Suspend execution here and wait for the threads to finish.
    receiver.join()
    # timer.cancel()

    control.socket.close()  # Close the socket

    print("Shut down complete.")

    sys.exit(0)
