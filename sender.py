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
from stp_helpers import Stp
from helpers import Helpers
from enums import SegmentType, LogActions

NUM_ARGS  = 7  # Number of command-line arguments
BUF_SIZE  = 4  # Size of buffer for receiving messages
MAX_SEQNO = 2**16 # Maximum sequence number

@dataclass
class Control:
    """Control block: parameters for the sender program."""
    # host: str               # Hostname or IP address of the receiver
    # ================== Update arguments =====================
    sender_port: int        # Port number of the sender
    rcvr_port: int      # Port number of the receiver
    max_win: int        # max window size, should be the same for receiver side
    rto: float          # retransmission time for a socket
    seqno: int          # sequence number of sender socket
    file_name: str      # name of file being sent
    rlp: float          # probability of incoming packet being dropped
    flp: float          # probability of sent packet being dropped
    socket: socket.socket   # Socket for sending/receiving messages
    is_connected: bool = False # a flag to signal successful connection or when to terminate
    start_time: float = 0.0   # time in miliseconds at first sent segment


# =====================Update setup_socket function ========================
def setup_socket(sender_port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # bind to sender port
    sock.bind(('127.0.0.1', sender_port))
    return sock

# Enter SYN_SENT state by first send an SYN segment
def state_syn_sent(control: Control):
    try:
        # Establish a connected UDP connection
        control.socket.connect(('127.0.0.1', control.rcvr_port))
        
        is_first_segment = True
        # To make the connection "reliable", we perform a two-way handshake.
        while not control.is_connected:
            try:
                # Create a STP segment
                stp_segment = Stp.create_stp_segment(type=SegmentType.SYN, seqno=control.seqno)
                # First send a SYN segment to signal establishment
                control.socket.send(stp_segment)

                if is_first_segment: 
                    control.start_time = Helpers.get_time_mls()
                    Helpers.log_message('sender', LogActions.SEND, 0.0, SegmentType.SYN, control.seqno, 0)
                    is_first_segment = False
                else:
                    Helpers.log_message('sender', LogActions.SEND, control.start_time, SegmentType.SYN, control.seqno, 0)


                # Set a timeout for next socket operation (i.e. recv())
                # If it takes longer than "rto" for receiver to response,
                # a TimeoutError will be raised.
                control.socket.settimeout(control.rto)
                
                response = control.socket.recv(BUF_SIZE)
                segtype, seqno, data = Stp.extract_stp_segment(response)

                if segtype == SegmentType.ACK:
                    Helpers.log_message('sender', LogActions.RECEIVE, control.start_time, SegmentType.ACK, seqno, 0)
                    control.is_connected = True
                    return
            except Exception as e:
                print(e)
                continue
            else:
                control.is_connected = True
            finally:
                control.socket.settimeout(None)
    except Exception as e:
        sys.exit(f"Failed to connect to '127.0.0.1':{rcvr_port}: {e}")


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

    Helpers.reset_log('sender')

    sock = setup_socket(sender_port)

    # Use a fixed seed for debugging purpose, NEED TO CHANGED BEFORE SUBMITTED
    random.seed(1)  # Seed the random number generator
    isn = random.randrange(MAX_SEQNO)

    # Create a control block for the sender program.
    control = Control(sender_port=sender_port, rcvr_port=rcvr_port, 
                      socket=sock, max_win=max_win, seqno=isn, rto=rto,
                      file_name=txt_file_to_send, flp=flp, rlp=rlp)
    state_syn_sent(control)
    print('Finished 2-way Connection Setup')
    # Start the receiver and timer threads.
    # receiver = threading.Thread(target=recv_thread, args=(control,))
    # receiver.start()

    # timer = threading.Timer(run_time, timer_thread, args=(control,))
    # timer.start()

    
    # Suspend execution here and wait for the threads to finish.
    # receiver.join()
    # timer.cancel()

    control.socket.close()  # Close the socket

    print("Shut down complete.")

    sys.exit(0)
