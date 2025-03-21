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
import traceback
import sys
import threading
import os
from dataclasses import dataclass
from src.helpers.arg_parser import ArgParser
from src.helpers.helpers import Helpers
from enums import LogActions, SegmentType
from src.helpers.stp_helpers import Stp


NUM_ARGS = 4  # Number of command-line arguments
BUF_SIZE = 1004  # Size of buffer for sending/receiving STP segments
MAX_SEQNO = 2**16 # Maximum sequence number
MSS = 1000 # Maximum segment (data) size
MSL = 1    # Maximum Segment Lifetime = 1 second 
@dataclass
class Control:
    """Control block: parameters for the receiver program."""
    # ================== Update arguments =====================
    rcvr_port:  int             # Port number of the receiver
    sender_port:int             # Port number of the sender
    output_file:str             # name of output file
    max_win:    int             # maximum window size for receiver buffer
    socket: socket
    start_time: float = 0.0     # Time at which first packet received
    is_alive: bool = True       # Flag variable, will be switched to False if it receive FIN segment.

class LRU_Acked_Cache:
    def __init__(self, max_queue_size: int) -> None:
        self.acked_map: dict[int, bool] = {}
        self.acked_queue: list[int] = []
        self.MAX_QUEUE_SIZE = max_queue_size

    def find(self, seqno: int) -> bool:
        '''
            Args:
                seqno (int): sequence number of a segment
            Returns:
                bool: returns True if recently received segment of seqno, False otherwise.
        '''
        return self.acked_map.get(seqno, False) != False

    def add_seqno(self, seqno: int) -> None:
        '''
            Add a recently received seqno into cache. If number of seqno saved exceeds (MAX_WIN/1000)*2, 
            pop the first elem out and delete it from dictionary.
            The choice of (MAX_WIN/1000)*2 might not be the most optimal number, but I just play safe here.
            Didn't check for duplicate as I assume it's relatively rare for duplicates to occur.

            Args:
                seqno (int): sequence number of a segment
            Returns:
                None
        '''
        self.acked_map[seqno] = True
        self.acked_queue.append(seqno)

        if len(self.acked_queue) == self.MAX_QUEUE_SIZE:
            lru_seqno = self.acked_queue.pop(0)
            self.acked_map.pop(lru_seqno)

        return
    

@dataclass
class Buffer:
    """Control block: parameters for the receiver buffer."""
    # ================== Update arguments =====================
    buffer:     list[bytes]    # Buffer that saves received data
    expct_seqno:int     # The expected sequence number when receive next packet
    index:      int     # The index where the next in-order packet lives in buffer
    max_size:   int     # The maximum size of buffer
    lru_seqno: LRU_Acked_Cache # a class to keep track of recently received Acked segments

def timeout_thread(control: Control):
    '''
        This function will be called after 2 seconds since receive of FIN
        to switch "is_alive" flag to false, which will terminate this program.
    '''
    control.socket.close()
    f.close()
    print('Receiver Closed!')
    os._exit(os.EX_OK)
    return


if __name__ == "__main__":
    if len(sys.argv) != NUM_ARGS + 1:
        sys.exit(f"Usage: {sys.argv[0]} rcvr_port sender_port txt_file_received max_win")

    # ================== Update arguments =====================
    rcvr_port = ArgParser.parse_port(sys.argv[1]) 
    sender_port = ArgParser.parse_port(sys.argv[2])
    txt_file_received = sys.argv[3]
    max_win = ArgParser.parse_max_win(sys.argv[4])
    max_buff_size = max_win // MSS
    # Open text file to write to
    f = open(txt_file_received, 'w')

    # ================== Update socket setup =====================
    Helpers.reset_log('receiver')
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(('127.0.0.1', rcvr_port))
        s.connect(('127.0.0.1', sender_port))
        control = Control(rcvr_port, sender_port, txt_file_received, max_win, socket=s)
        print('Receiver socket opened!')
        
        is_first_segment = True
        control.start_time = Helpers.get_time_mls()
        while control.is_alive:
            receive = control.socket.recv(BUF_SIZE)
            segmentType, seqno, data = Stp.extract_stp_segment(receive)
            if is_first_segment:
                is_first_segment = False
                # First rcv message must always be a SYN segment
                Helpers.log_message('receiver', LogActions.RECEIVE, 0.0, SegmentType.SYN, seqno, 0)
            else:
                Helpers.log_message('receiver', LogActions.RECEIVE, control.start_time, segmentType, seqno, 0 if not data else len(data))            


            if segmentType == SegmentType.SYN:
                print('receieve SYN from sender')
                # For SYN segment, add 1 to seqno
                seqno = Helpers.add_seqno(seqno, 1)

                # Send back ACK segment
                ack_segment = Stp.create_stp_segment(SegmentType.ACK, seqno)
                s.send(ack_segment)

                Helpers.log_message('receiver', LogActions.SEND, control.start_time, SegmentType.ACK, seqno, 0)

                # Initialize buffer
                buff = Buffer([None] * max_buff_size, seqno, 0, max_buff_size, LRU_Acked_Cache(max_buff_size * 2))
            elif segmentType == SegmentType.FIN:
                print('receive FIN from sender')
                # For FIN segment, add 1 to seqno
                seqno = Helpers.add_seqno(seqno, 1)

                # Send back ACK segment
                ack_segment = Stp.create_stp_segment(SegmentType.ACK, seqno)
                s.send(ack_segment)

                Helpers.log_message('receiver', LogActions.SEND, control.start_time, SegmentType.ACK, seqno, 0)

                timer = threading.Timer(2 * MSL, timeout_thread, args=(control,))
                timer.start()
            elif segmentType == SegmentType.DATA:
                # Need to handle negative MOD
                print('receieve DATA from sender')
                print(seqno, buff.expct_seqno)
                # If in-order packet, place it to buffer[index]
                if seqno == buff.expct_seqno:
                    if buff.buffer[buff.index] != None: 
                        raise Exception("buffer[index] is not empty")
                    
                    buff.buffer[buff.index] = data
                    # Iterate thru buffer to write all in-order data
                    while buff.buffer[buff.index] != None:
                        buffered_rcv_data = buff.buffer[buff.index]
                        buff.lru_seqno.add_seqno(buff.expct_seqno)
                        
                        current_seqno = (buff.expct_seqno + len(buffered_rcv_data)) % MAX_SEQNO

                        f.write(buffered_rcv_data.decode())

                        # Re-empty this position in buffer
                        buff.buffer[buff.index] = None

                        buff.expct_seqno = current_seqno
                        buff.index = (buff.index + 1) % buff.max_size
                elif not buff.lru_seqno.find(seqno):
                    # If this is an out-of-order packet (by checking whether it exists in our lru cache), place it at somewhere with respect to 
                    # the position of the expected in-order data
                    
                    # For example, we are expecting packet seqno = 1000 at index 1,
                    # But receives packet seqno = 4000. 
                    # Hence, we need to place this new packet at index = (4000-1000)/MSS + 1 (index) = 4
                    
                    # First, find the difference between the received seqno and the expected seqno.
                    seqno_diff = seqno - buff.expct_seqno

                    # Since sequence numbers are MOD-ED by 2^16, there are cases where seqno is smaller
                    # than expected seqno, result in negative "seqno_diff"

                    # In this case, we just need to add MAX_SEQNO to bump it up
                    if seqno_diff < 0:
                        # For example, expected seqno is 4000 at index 1.
                        # But receives packet seqno = 1000.
                        # Hence, seqno_diff = 1000 - 4000 = -3000. Then add MAX_SEQNO => seqno_diff = 2000.
                        # Divide it by MSS, the index offset is 2, so the index for this packet seqno = 1000 is 3.
                        # 0 1(expct) 2 3(new) 4
                        #   4000       1000
                        seqno_diff += MAX_SEQNO
                    
                    final_index = (buff.index + (seqno_diff // MSS)) % buff.max_size
                    print(final_index)
                    if buff.buffer[final_index] != None:
                        raise Exception('buffer[final_index] is not empty')

                    buff.buffer[final_index] = data
                else:
                    # Getting to this means that we received an already ACKED segment, so we don't do anything here
                    pass

                # Send back an ACK segment
                ack_segment = Stp.create_stp_segment(SegmentType.ACK, buff.expct_seqno)
                s.send(ack_segment)
                Helpers.log_message('receiver', LogActions.SEND, control.start_time, SegmentType.ACK, buff.expct_seqno, 0)
    except Exception as e:
        traceback.print_exc()