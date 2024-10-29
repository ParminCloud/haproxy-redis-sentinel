import socket

__all__ = ["send_command"]


def encode_command(command: str) -> bytes:
    return f"{command};\n".encode("utf-8")


def recvall(sock: socket.socket):
    BUFF_SIZE = 1024
    data = b''
    while True:
        part = sock.recv(BUFF_SIZE)
        data += part
        if len(part) < BUFF_SIZE:
            # either 0 or end of data
            break
    return data


def send_command(addr: str, command: str) -> str:
    if len(addr.split(":")) == 2:
        addr_parts = addr.split(":")
        a = (addr_parts[0], int(addr_parts[1]))
        family = socket.AF_INET
    else:
        a = addr
        family = socket.AF_UNIX
    unix_socket = socket.socket(family, socket.SOCK_STREAM)
    unix_socket.settimeout(10)
    unix_socket.connect(a)

    unix_socket.send(encode_command(command))

    return recvall(unix_socket).decode("utf-8").strip()
