import ipaddress


def valid_ip_network(network):
    """Take a v4 or v6 network, e.g. '192.168.3.5/24' or
    '192.168.3.5/255.255.255.0' and return whether it is valid.

    Args:
        network (str): IP address and mask, e.g. '192.168.3.5/24'.

    Returns:
        True if valid, False otherwise.
    """
    try:
        ipaddress.ip_network(network, strict=False)
    except ValueError:
        return False

    return True
