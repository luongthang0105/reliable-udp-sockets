import sys
import threading
from sender import Control, SegmentControl, BUF_SIZE, MSS
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

class Est_Threads:
    @staticmethod 
    def send_thread(control: Control, segment_control: SegmentControl):
        segment_control.end = control.max_win / MSS
        # Index within the sliding window
        index = 0
        # Number of segments
        num_segments = len(segment_control.segments)
        while index < num_segments and segment_control.end < num_segments:
            if index < segment_control.end:
                data = segment_control.segments[index]
                Helpers.send_data(control, control.seqno, data)
                index += 1
                control.seqno += len(data)
        return

    @staticmethod
    def recv_thread(control: Control, segment_control: SegmentControl):
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
        data = segment_control.segments[segment_index]
        # Resend this segment
        Helpers.send_data(control, unACKed_seqno, data)
        

