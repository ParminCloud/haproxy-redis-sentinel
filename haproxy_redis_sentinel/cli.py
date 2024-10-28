import typer
from rich.console import Console
from datetime import datetime
import redis
from redis.retry import Retry
from redis.backoff import ExponentialBackoff
from typing import Annotated, Any
import socket

__all__ = ["app"]

app = typer.Typer()

err_console = Console(stderr=True)
out_console = Console(stderr=False)


def encode_command(command: str) -> bytes:
    return f"{command};\n".encode("utf-8")


def log_prefix() -> str:
    return f"{datetime.now().strftime("%c")} "


def info(msg):
    typer.echo(
        log_prefix() + typer.style(
            msg,
            fg=typer.colors.GREEN,
            bold=True
        ),
        err=False
    )


def error(msg: str):
    typer.echo(
        log_prefix() + typer.style(
            msg,
            fg=typer.colors.WHITE,
            bg=typer.colors.RED,
            bold=True
        ),
        err=True
    )


def recvall(sock: socket.socket):
    BUFF_SIZE = 1024
    data = b''
    while True:
        part = sock.recv(BUFF_SIZE)
        data += part
        print(part)
        if len(part) < BUFF_SIZE:
            # either 0 or end of data
            break
    return data


def send_command(addr: str, command: str) -> str:
    if len(addr.split(":")) == 2:
        family = socket.AF_INET
        addr_parts = addr.split(":")
        a = (addr_parts[0], int(addr_parts[1]))
    else:
        a = addr
        family = socket.AF_UNIX
    unix_socket = socket.socket(family, socket.SOCK_STREAM)
    unix_socket.settimeout(10)
    unix_socket.connect(a)

    unix_socket.send(encode_command(command))

    return recvall(unix_socket).decode("utf-8")


@app.command()
def run(
    sentinel_host: Annotated[
        str,
        typer.Option(
            "--sentinel-host",
            "-h",
            help="Sentinel Hostname",
            envvar="SENTINEL_HOST",
            rich_help_panel="Sentinel Info"
        )] = "127.0.0.1",
    sentinel_port: Annotated[
        int,
        typer.Option(
            "--sentinel-port",
            "-p",
            help="Sentinel Port",
            envvar="SENTINEL_PORT",
            rich_help_panel="Sentinel Info"
        )] = 26379,
    sentinel_password: Annotated[
        str | None,
        typer.Option(
            "--sentinel-password",
            "-p",
            help="Sentinel Password",
            envvar="SENTINEL_PASSWORD",
            hide_input=True,
            rich_help_panel="Sentinel Info"
        )] = None,
    master_name: Annotated[
        str,
        typer.Option(
            "--master-name",
            "-m",
            help="Sentinel Master name",
            envvar="MASTER_NAME",
            rich_help_panel="Sentinel Info"
        )] = "mymaster",
    haproxy_socket: Annotated[
        str,
        typer.Option(
            "--haproxy-socket",
            help="HAProxy admin socket address",
            envvar="HAPROXY_SOCKET",
            rich_help_panel="HAProxy Info"
        )] = "/var/run/haproxy/haproxy.sock",
    haproxy_backend: Annotated[
        str,
        typer.Option(
            "--haproxy-backend",
            help="HAProxy Backend name to control (Set it to an empty backend)",  # noqa: E501
            envvar="HAPROXY_BACKEND",
            rich_help_panel="HAProxy Info"
        )] = "redis_master",
    haproxy_server_name: Annotated[
        str,
        typer.Option(
            "--haproxy-server-name",
            help="HAProxy Server name to control, It will be added and controlled throw given backend",  # noqa: E501
            envvar="HAPROXY_SERVER_NAME",
            rich_help_panel="HAProxy Info"
        )] = "current_master",
):
    conn = redis.Redis(
        host=sentinel_host,
        port=sentinel_port,
        password=sentinel_password,
        decode_responses=True,
        retry=Retry(ExponentialBackoff(), 3),
    )
    address = None
    sentinel_info: dict[str, Any] = conn.info()  # type: ignore
    for k in sentinel_info.keys():
        if k.startswith("master") and sentinel_info[k]["name"] == master_name:
            address = sentinel_info[k]["address"]
    info(address)
    info(send_command(haproxy_socket, f"del server {
         haproxy_backend}/{haproxy_server_name}"))
    info(send_command(haproxy_socket,
         f"add server {haproxy_backend}/{haproxy_server_name} {address}"))
    pubsub = conn.pubsub()
    pubsub.subscribe("+switch-master")
    for message in pubsub.listen():
        if not isinstance(message["data"], str):
            continue
        data: list[str] = message["data"].split(" ")
        if data[0] != master_name:
            info("Skipping master change: Master name did not matched")
            continue
        host = data[3]
        port = data[4]
        info("Master Changed, Terminating clients")
        info(send_command(haproxy_socket,
             "shutdown sessions server redis_master/current_master"))
        info(f"Switching to new master Host: {host}, Port: {port}")
        info(send_command(haproxy_socket,
                          f"set {haproxy_backend}/{haproxy_server_name} addr {host} port {port}"))  # noqa: E501
