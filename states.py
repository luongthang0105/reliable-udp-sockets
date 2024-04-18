import sys
import threading
from sender_prototypes import Control, SegmentControl, BUF_SIZE, MSS
from stp_helpers import Stp
from enums import SegmentType, LogActions
from helpers import Helpers

class States:
    @staticmethod
    def state_syn_sent(control: Control):
        '''
        Enter SYN_SENT state by first sending an SYN segment, waiting for ACK from receiver.
        '''
        try:
            # Establish a connected UDP connection
            control.socket.connect(('127.0.0.1', control.rcvr_port))
            
            # A flag to mark first segment. We need this because the time of the first log message is 0.0
            is_first_segment = True
            # To make the connection "reliable", we perform a two-way handshake.
            while not control.is_connected:
                try:
                    # Create a STP segment
                    stp_segment = Stp.create_stp_segment(segtype=SegmentType.SYN, seqno=control.seqno)
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
                    segtype, seqno, _ = Stp.extract_stp_segment(response)

                    if segtype == SegmentType.ACK:
                        Helpers.log_message('sender', LogActions.RECEIVE, control.start_time, SegmentType.ACK, seqno, 0)
                        control.is_connected = True
                        control.seqno = seqno
                except Exception as e:
                    print(e)
                    continue
                else:
                    control.is_connected = True
                finally:
                    control.socket.settimeout(None)
        except Exception as e:
            sys.exit(f"Failed to connect to '127.0.0.1':{control.rcvr_port}: {e}")

    @staticmethod
    def state_est(control: Control):
        control.is_est_state = True

        segment_control = Helpers.create_segment_control(control.file_name, control.seqno)

        # Start the receiver and sender threads.
        send = threading.Thread(target=Est_Threads.send_thread, args=(control, segment_control,))
        send.start()

        receiver = threading.Thread(target=Est_Threads.recv_thread, args=(control, segment_control))
        receiver.start()

        # timer = threading.Timer(1, Est_Threads.timeout_thread, args=(control,))
        # timer.start()
        # timer.

        
        # Suspend execution here and wait for the threads to finish.
        receiver.join()
        send.join()
        # timer.cancel()

def send_data(control: Control, segment_control: SegmentControl, data_seqno: int, data: bytes):
    '''
        Send data to receiver, initiate timer if haven't already.

        Args:
            control (Control): The control block for the sender program.
            segment_control (SegmentControl): The control block for data segments.
            data_seqno  (int): sequence number of the data we wanna send
            data        (bytes): payload
    '''
    sent_segment = Stp.create_stp_segment(SegmentType.DATA, data_seqno, data)

    control.lock.acquire()

    if control.timer == None:
        print(f'put timer on {data_seqno}')
        control.timer = threading.Timer(control.rto, Est_Threads.timeout_thread, args=(control, segment_control, data_seqno))
        control.timer.start()
    control.lock.release()

    if Helpers.is_dropped(control.flp):
        Helpers.log_message('sender', LogActions.DROPPED, control.start_time, SegmentType.DATA, data_seqno, len(data))
    else:
        # print(f'send/timer put timeout for {data_seqno}')
        Helpers.log_message('sender', LogActions.SEND, control.start_time, SegmentType.DATA, data_seqno, len(data))
        control.socket.send(sent_segment)


class Est_Threads:
    @staticmethod 
    def send_thread(control: Control, segment_control: SegmentControl):
        segment_control.end = control.max_win / MSS
        # Index within the sliding window
        index = 0
        # Number of segments
        num_segments = len(segment_control.segments)
        while index < num_segments and segment_control.send_base < num_segments:
            if index < segment_control.end:
                data = segment_control.segments[index].data
                segment_control.segments[index].is_sent = True
                send_data(control, segment_control, control.seqno, data)
                index += 1
                control.seqno = Helpers.add_seqno(control.seqno, len(data))

        return

    @staticmethod
    def recv_thread(control: Control, segment_control: SegmentControl):
        """The receiver thread function.

        The recv_thread() function is the entry point for the receiver thread. It
        will sit in a loop, checking for messages from the receiver. When a message 
        is received, the sender will unpack the message and print it to the log. 
    
        Args:
            control (Control): The control block for the sender program.
            segment_control (SegmentControl): The control block for data segments.
        """
        while control.is_est_state:
            received_segment = control.socket.recv(BUF_SIZE)
            segment_type, seqno, _ = Stp.extract_stp_segment(received_segment)

            if Helpers.is_dropped(control.rlp):
                Helpers.log_message('sender', LogActions.DROPPED, control.start_time, segment_type, seqno, 0)
                continue

            Helpers.log_message('sender', LogActions.RECEIVE, control.start_time, segment_type, seqno, 0)
            
            # Get the index of the received segment in segments[] via their seqno
            # If the seqno doesnt exist in the map, then this segment should be the very last one of the file.
            # Hence, let received_segment_index be the length of segments[] (why? will explain in next few lines)
            segments_len = len(segment_control.segments)
            received_segment_index = segment_control.seqno_map.get(seqno, segments_len)

            if segment_control.send_base < received_segment_index:
                control.lock.acquire()

                if control.timer != None: 
                    control.timer.cancel()
                    control.timer = None
                # If there are any unACKed segments, put timer on it
                if received_segment_index <= min(segment_control.end, segments_len - 1) and segment_control.segments[received_segment_index].is_sent:
                    print(f'recv put timer on {seqno}')
                    control.timer = threading.Timer(control.rto, Est_Threads.timeout_thread, args=(control, segment_control, seqno))
                    control.timer.start()
                
                control.lock.release()

                free_slots = received_segment_index - segment_control.send_base
                # Since "send_base" is set to be equal to "receive_segment_index",
                # we know that if "receive_segment_index" == len(segments) then 
                # send_base == len(segments) as well. 
                # Having send_base equal to that value means that we already sent all data,
                # which will terminate the send_thread.
                segment_control.send_base = received_segment_index
                segment_control.end += free_slots
                segment_control.dupACK_cnt = 0

            elif segment_control.send_base == received_segment_index:
                # print(segment_control.dupACK_cnt)
                segment_control.dupACK_cnt += 1
                # Fast retransmit
                if segment_control.dupACK_cnt == 3:
                    fast_retrans_data = segment_control.segments[received_segment_index].data

                    send_data(control, segment_control, seqno, fast_retrans_data)
                    print(f'dupACK for {seqno}')
                    
                    segment_control.dupACK_cnt = 0
    @staticmethod
    def timeout_thread(control: Control, segment_control: SegmentControl, unACKed_seqno: int):
        """ If enters this thread, the waiting for some unACKed segment exceeds time limit (rto).
        We then retransmit oldest unACKed segment, restart timer, and reset dup ACK count.
        Args:
            control (Control): The control block for the sender program.
            segment_control (SegmentControl): The control block for data segments.
            unACKed_seqno (int): The oldest unACKed sequence number.
        """
        segment_control.dupACK_cnt = 0

        # Should we cancel any timer? Maybe not
        segment_index = segment_control.seqno_map[unACKed_seqno]
        data = segment_control.segments[segment_index].data
        # Resend this segment
        print(f'timeout for {unACKed_seqno}')
        
        control.lock.acquire()
        control.timer = None
        control.lock.release()

        send_data(control, segment_control, unACKed_seqno, data)
        

