from handler import Handler
from typing import Annotated
import typer

__all__ = ["app"]

app = typer.Typer()


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
    handler = Handler(
        sentinel_host=sentinel_host,
        sentinel_port=sentinel_port,
        sentinel_password=sentinel_password,
        master_name=master_name,
        haproxy_socket=haproxy_socket,
        haproxy_backend=haproxy_backend,
        haproxy_server_name=haproxy_server_name
    )
    handler.set_initial_server()
    handler.start_worker()
