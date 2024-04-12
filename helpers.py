import time
from enums import LogActions, SegmentType
# General helper functions
MAX_SEQNO = 2**16
class Helpers:
    @staticmethod
    def get_time_mls() -> float:
        '''
            Returns:
                float: miliseconds (2 decimal place) since the epoch
        '''
        return round(time.time() * 1000, 2)
    
    @staticmethod
    def log_message(user: str, action: LogActions, start_time: float, segment_type: SegmentType, seqno: int, num_bytes: int) -> None:
        '''
            Args:
                user            (str)           : 'sender' or 'receiver', based on which socket calls this method 
                action          (LogActions)    : either 'snd'(SEND), 'rcv'(RECEIVE), or 'drp'(DROP)
                start_time      (float)         : start time of the first segment
                segment_type    (SegmentType)   : either DATA, ACK, SYN, FIN
                seqno           (int)           : sequence number
                num_bytes       (int)           : payload size
            Returns:
                None
        '''
        log_file = f"{user}_log.txt"
        time_diff = Helpers.get_time_mls() - start_time
        with open(log_file, 'a') as file:
            file.write(f"{action.value} {time_diff} {segment_type.name} {seqno} {num_bytes}\n")
        return
    
    @staticmethod
    def reset_log(user: str) -> None:
        '''
            Empty a log file by opening it in 'write' mode.

            Args:
                user            (str)           : 'sender' or 'receiver', based on which socket calls this method 
            Returns:
                None
        '''
        log_file = f"{user}_log.txt"
        with open(log_file, 'w') as file:
            pass
        return
    
    @staticmethod
    def add_seqno(seqno: int, amount: int) -> int:
        '''
            Args:
                seqno (int): current sequence number
                amount(int): amount of bytes added to seqno
            Returns:
                int: resulted seqno after addition (and MOD MAX_SEQNO) 
        '''
        return (seqno + amount) % MAX_SEQNO
