# General helper functions
MAX_SEQNO = 2**16
class Helpers:
    @staticmethod
    def log_message(user: str, action: str, time: float, segment_type: str, seqno: int, num_bytes: int) -> None:
        log_file = f"{user}_log.txt"
        with open(log_file, 'a') as file:
            file.write(f"{action} {time} {segment_type} {seqno} {num_bytes}\n")
        return
    
    @staticmethod
    def reset_log(user: str) -> int:
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
