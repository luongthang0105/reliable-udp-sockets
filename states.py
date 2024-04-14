import sys
from sender import Control, BUF_SIZE
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
