import sys

def parse_port(port_str, min_port=49152, max_port=65535):
    """Parse the port argument from the command-line.

    The parse_port() function will attempt to parse the port argument
    from the command-line into an integer. If the port argument is not 
    numerical, or within the acceptable port number range, the program will
    terminate with an error message.

    Args:
        port_str (str): The port argument from the command-line.
        min_port (int, optional): Minimum acceptable port. Defaults to 49152.
        max_port (int, optional): Maximum acceptable port. Defaults to 65535.

    Returns:
        int: The port as an integer.
    """
    try:
        port = int(port_str)
    except ValueError:
        sys.exit(f"Invalid port argument, must be numerical: {port_str}")
    
    if not (min_port <= port <= max_port):
        sys.exit(f"Invalid port argument, must be between {min_port} and {max_port}: {port}")

    return port

def parse_file_name(file_name):
    """Parse the txt_file_to_send argument from the command-line.

    This function tries to open the file with the given file name.
	If it fails to do so, then the file itself may not exist or may be corrupted.

    Args:
        file_name (str): The txt_file_to_send argument from the command-line.

    Returns:
        str: file name
    """
    try:
        f = open(file_name, "r")
    except Exception as e:
        sys.exit(e)

    return file_name

def parse_max_win(max_win_str):
    """Parse the max_win argument from the command-line.

    This function needs to check whether max_win size >= 1000 and max_win is a multiple of 1000 bytes.

    Args:
        max_win_str (str): The max_win argument from the command-line.

    Returns:
        int: max_win
    """
    max_win = int(max_win_str)
    if max_win < 1000 or max_win % 1000 != 0:
        sys.exit(f"Invalid max_win, must be greater than or equal to 1000 and be a multiple of 1000 bytes: {max_win}")

    return max_win

def parse_rto(rto_str):
    """Parse the rto argument from the command-line.

    This function needs to check whether rto >= 0.

    Args:
        rto_str (str): The rto (retransmission timer) argument from the command-line.

    Returns:
        int: rto
    """
    rto = int(rto_str)
    if rto < 0:
        sys.exit(f"Invalid rto, must be an unsigned integer: {rto}")
    return rto

def parse_prop(prop_str):
    """Parse the flp/rlp argument from the command-line.

    This function needs to check whether the probability >= 0.

    Args:
        prop_str (str): The flp/rlp argument from the command-line.

    Returns:
        float: prop
    """
    prop = float(prop_str)
    if not (0.0 <= prop <= 1.0):
        sys.exit(f'Invalid flp/rlp, must be between 0 and 1 (inclusive): {prop_str}')
    return prop