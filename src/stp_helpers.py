from enums import SegmentType

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
    # In normal methods within a function, we need "self" as a parameter.
    # Hence, use @staticmethod decorator to remove the need of self parameter.
    # This will also allow us to use these methods without initializing a class.
    @staticmethod
    def create_stp_segment(segtype: SegmentType, seqno: int, data: bytes = None) -> bytes:
        """Create a STP segment that obeys the above diagram, given the types, seqno and data (payload).
        
        This function converts the type and segno to bytes and append it with data.

        Args:
            type  (int): Type of this segment, either DATA = 0, ACK = 1, SYN = 2, and FIN = 3.  
            seqno (int): The sequence number of this segment.
            data  (bytes): Part of data from txt file in bytes.

        Returns:
            bytes: STP Segment in bytes.
        """
        type_bytes = segtype.value.to_bytes(2, byteorder="big")
        seqno_bytes = seqno.to_bytes(2, byteorder="big")
        stp_segment = type_bytes + seqno_bytes
        if data:
            # print(type(stp_segment), type(data))
            stp_segment = stp_segment + data
        return stp_segment
    
    @staticmethod
    def extract_stp_segment(stp_segment: bytes):
        """Extract segment type, sequence number and payload from received STP segment. 
        Data maybe None if received segment is a SYN, FIN, or ACK segment.

        Args:
            stp_segment (bytes): received STP segment.

        Returns:
            SegmentType : type of this segment, either SYN, FIN, ACK or DATA.
            int         : sequence number of this segment
            bytes       : received payload
        """
        segmentType = SegmentType(int.from_bytes(stp_segment[:2], 'big'))
        seqno = int.from_bytes(stp_segment[2:4], 'big')

        if len(stp_segment) > 4: data = stp_segment[4:]
        else: data = None

        return segmentType, seqno, data