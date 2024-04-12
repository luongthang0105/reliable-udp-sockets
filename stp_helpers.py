# Class Stp (simple transfer protocol) which contains methods that facilitates the use of protocol.
class Stp:
    # Create a STP Segment where:
    #  +--------------------+--------------------+
    #  |                 Byte Offset             |
    #  +------+------+------+------+------+------+
    #  |   0  |   1  |   2  |  3   |  next 1KB   |
    #  +------+------+------+------+------+------+
    #  |    type     |    seqno    |    data     |
    #  +-------------+------+-------------+------+
    def create_stp_segment(type: int, seqno: int, data: bytes = None) -> bytes:
        """Create a STP segment that obeys the above diagram, given the types, seqno and data (payload).
        
        This function converts the type and segno to bytes and append it with data.

        Args:
            type  (int): Type of this segment, either DATA = 0, ACK = 1, SYN = 2, and FIN = 3.  
            seqno (int): The sequence number of this segment.
            data  (bytes): Part of data from txt file in bytes.

        Returns:
            bytes: STP Segment in bytes.
        """
        type_bytes = type.to_bytes(2, byteorder="big")
        seqno_bytes = seqno.to_bytes(2, byteorder="big")
        stp_segment = type_bytes + seqno_bytes
        if not data:
            stp_segment += data
        return stp_segment