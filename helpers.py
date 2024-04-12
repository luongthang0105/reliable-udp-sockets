# General helper functions
class Helpers:
    def log_message(user: str, action: str, time: float, segment_type: str, seqno: int, num_bytes: int):
        log_file = f"{user}_log.txt"
        with open(log_file, 'a') as file:
            file.write(f"{action} {time} {segment_type} {seqno} {num_bytes}\n")
    
    def reset_log(user):
        log_file = f"{user}_log.txt"
        with open(log_file, 'w') as file:
            pass
        return
