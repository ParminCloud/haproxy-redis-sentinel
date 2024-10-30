from enum import StrEnum
from haproxy_redis_sentinel.logging import info
from haproxy_redis_sentinel.utils import send_command
from redis.backoff import ExponentialBackoff
from redis.retry import Retry
from typing import Annotated, Any
import redis
import typer


__all__ = ["app"]

app = typer.Typer()


class HAProxyOutput(StrEnum):
    SERVER_REGISTERED = "New server registered."
    SERVER_DELETED = "Server deleted."
    SERVER_NOT_FOUND = "No such server."


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
            "-P",
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
    try:
        master_id = [k for k in sentinel_info.keys()
                     if k.startswith("master") and
                     sentinel_info[k]["name"] == master_name][0]
    except IndexError:
        raise Exception("Unable to find given master by name")
    address = sentinel_info[master_id]["address"]
    info(f"Setting initial master address: {address}")

    # Remove server in case of restarts
    out = send_command(haproxy_socket, f"del server {
        haproxy_backend}/{haproxy_server_name}")
    if out not in {HAProxyOutput.SERVER_DELETED,
                   HAProxyOutput.SERVER_NOT_FOUND}:
        raise Exception(f"Error while removing old server: {out}")
    out = send_command(haproxy_socket,
                       f"add server {haproxy_backend}/{haproxy_server_name} {address}")  # noqa: E501
    if out != HAProxyOutput.SERVER_REGISTERED:
        raise Exception(f"Error while adding initial server: {out}")
    info(out)
    pubsub = conn.pubsub()
    pubsub.subscribe("+switch-master")
    for message in pubsub.listen():
        if not isinstance(message["data"], str):
            info("Skipping initial message in Pub/Sub")
            continue
        data: list[str] = message["data"].split(" ")
        if data[0] != master_name:
            info("Skipping master change: Master name did not matched")
            continue
        host = data[3]
        port = data[4]
        info("Master Changed, Terminating clients")
        info(send_command(haproxy_socket,
             "set server redis_master/current_master state maint"))
        info(send_command(haproxy_socket,
             "shutdown sessions server redis_master/current_master"))
        info(f"Switching to new master Host: {host}, Port: {port}")
        info(send_command(haproxy_socket,
                          f"set server {haproxy_backend}/{haproxy_server_name} addr {host} port {port}"))  # noqa: E501
