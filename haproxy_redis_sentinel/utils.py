import socket
import re

__all__ = ["send_command", "is_empty", "is_ipv4"]


def is_ipv4(ip: str) -> bool:
    """
    Check if a given string is a valid IP address.
        :param ip: IP address to check
        :return: True if valid, False otherwise
    """
    pattern = re.compile(
        r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"  # noqa: E501
    )
    return bool(pattern.match(ip))


def encode_command(command: str) -> bytes:
    """
    Encode a command string into bytes.
        :param command: Command string to encode
        :return: Encoded command as bytes
    """
    return f"{command};\n".encode("utf-8")


def recvall(sock: socket.socket) -> bytes:
    """
    Receive all data from a socket until EOF.
        :param sock: Socket to receive data from
        :return: Received data as bytes
    """
    BUFF_SIZE = 1024
    data = b''
    while True:
        part = sock.recv(BUFF_SIZE)
        data += part
        if len(part) < BUFF_SIZE:
            # either 0 or end of data
            break
    return data


def send_command(addr: str, command: str | list[str]) -> str:
    """
    Send a command to a socket address and return the response.
        :param addr: Socket address (IP:port or path)
        :param command: Command to send (string or list of strings)
        :return: Response from the socket
    """
    result = ""
    if len(addr.split(":")) == 2:
        addr_parts = addr.split(":")
        a = (addr_parts[0], int(addr_parts[1]))
        family = socket.AF_INET
    else:
        a = addr
        family = socket.AF_UNIX
    unix_socket = socket.socket(family, socket.SOCK_STREAM)
    unix_socket.settimeout(10)
    try:
        unix_socket.connect(a)
        if not isinstance(command, str):
            command = ";".join(command)
        unix_socket.send(encode_command(command))
        result = recvall(unix_socket).decode("utf-8").strip()
    except Exception as e:
        unix_socket.close()
        raise e
    finally:
        unix_socket.close()
    return result


def is_empty(value):
    """
    Check if a value is empty.
        :param value: Value to check
        :return: True if empty, False otherwise
    """
    return value in (None, "", [], {})
