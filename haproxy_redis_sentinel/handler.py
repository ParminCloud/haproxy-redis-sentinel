from time import sleep
from typing import Any
from enum import StrEnum
from utils import send_command
from redis import Redis
from redis.retry import Retry
from redis.backoff import FullJitterBackoff
from multiprocessing import Process
from logger import info, error
import orjson


class HAProxyOutput(StrEnum):
    SERVER_REGISTERED = "New server registered."
    SERVER_DELETED = "Server deleted."
    SERVER_NOT_FOUND = "No such server."
    BACKEND_NOT_FOUND = 'No such backend.'


class Handler(object):
    def __init__(
        self,
        sentinel_host: str = "127.0.0.1",
        sentinel_port: int = 26379,
        sentinel_password: str | None = None,
        master_name: str = "mymaster",
        haproxy_socket: str = "/var/run/haproxy/haproxy.sock",
        haproxy_backend: str = "redis_master",
        haproxy_server_name: str = "current_master",
    ) -> None:
        self.conn = Redis(
            host=sentinel_host,
            port=sentinel_port,
            password=sentinel_password,
            decode_responses=True,
            retry=Retry(FullJitterBackoff(), 5),
        )
        self.master_name = master_name
        self.haproxy_socket = haproxy_socket
        self.haproxy_backend = haproxy_backend
        self.haproxy_server_name = haproxy_server_name

    def get_master_address(self) -> str:
        address = None
        sentinel_info: dict[str, Any] = self.conn.info()  # type: ignore
        try:
            master_id = [
                k for k in sentinel_info.keys()
                if k.startswith("master") and
                sentinel_info[k]["name"] == self.master_name
            ][0]
        except IndexError:
            raise Exception("Unable to find given master by name")
        address = sentinel_info[master_id]["address"]

        return address

    def send_command(self, commands: str | list[str], log_data=True) -> str:
        out = send_command(self.haproxy_socket, commands)
        if log_data:
            info(f"HAProxy command: {commands}, Output: {out}")
        return out

    def shutdown_current_server(self) -> str:
        return self.send_command(
            [
                f"set server {self.haproxy_backend}/{self.haproxy_server_name} state maint",  # noqa: E501
                f"shutdown sessions server {self.haproxy_backend}/{self.haproxy_server_name}",  # noqa: E501
            ]
        )

    def remove_current_server(
            self,
            ignore_notfound: bool = True,
            shutdown: bool = True,
    ) -> None:
        out = ""
        if shutdown:
            out = self.shutdown_current_server()
        out += self.send_command(
            f"del server {self.haproxy_backend}/{self.haproxy_server_name}",
        )
        ignored_outputs = {
            HAProxyOutput.SERVER_DELETED,
            HAProxyOutput.SERVER_NOT_FOUND,
        }
        if ignore_notfound:
            ignored_outputs.add(HAProxyOutput.BACKEND_NOT_FOUND)

        if len(out) > 0 and not any(item in out for item in ignored_outputs):
            raise Exception(f"Error while removing old server: {out}")

    def add_server(self, address: str):
        out = self.send_command(
            f"add server {self.haproxy_backend}/{self.haproxy_server_name} {address}"  # noqa: E501
        )
        if out != HAProxyOutput.SERVER_REGISTERED:
            raise Exception(f"Error while adding initial server: {out}")
        self.send_command(
            f"enable server {self.haproxy_backend}/{self.haproxy_server_name} {address}"  # noqa: E501
        )

    def set_server_address(self, host: str, port: int):
        self.send_command(
            [
                f"set server {self.haproxy_backend}/{self.haproxy_server_name} addr {host}",  # noqa: E501
                f"set server {self.haproxy_backend}/{self.haproxy_server_name} port {port}",  # noqa: E501
                f"set server {self.haproxy_backend}/{self.haproxy_server_name} state ready",  # noqa: E501
            ]
        )

    def subscriber(self):
        pubsub = self.conn.pubsub()
        pubsub.subscribe("+switch-master")
        for message in pubsub.listen():
            data = message["data"]
            if not isinstance(data, str):
                continue
            master_info: list[str] = message["data"].split(" ")
            if master_info[0] != self.master_name:
                continue
            self.shutdown_current_server()
            self.set_server_address(master_info[3], int(master_info[4]))

    def set_initial_server(self):
        self.remove_current_server()
        return self.add_server(self.get_master_address())

    def haproxy_server_checker(self):
        stats: list[list[dict | None] | None] | None = orjson.loads(
            self.send_command(
                f"show stat {self.haproxy_backend} 4 -1 json",
                log_data=False,
            )
        )
        if stats in (None, [], {}):
            return self.set_initial_server()
        for group in stats:
            if group in (None, [], {}):
                return self.set_initial_server()
            for item in group:
                if (item is None) or (not isinstance(item, dict)):
                    continue
                field = item.get("field", {})
                if (field is None) or (not isinstance(field, dict)):
                    continue
                if field.get("name") == "addr":
                    addr_value = item.get("value", {}).get("value", "")
                    if not addr_value or len(addr_value) < 0:
                        return self.set_initial_server()

    def haproxy_server_checker_worker(self):
        while True:
            self.haproxy_server_checker()
            sleep(2)

    def start_worker(self):
        subscriber_process = Process(target=self.subscriber, name="subscriber")
        haproxy_server_checker_process = Process(
            target=self.haproxy_server_checker_worker,
            name="haproxy_server_checker",
        )
        subscriber_process.start()
        haproxy_server_checker_process.start()

        try:
            while True:
                if not subscriber_process.is_alive():
                    error(f"{subscriber_process.name} died. Exiting.")
                    haproxy_server_checker_process.terminate()
                    exit(1)

                if not haproxy_server_checker_process.is_alive():
                    error(f"{haproxy_server_checker_process.name} died. Exiting.")  # noqa: E501
                    subscriber_process.terminate()
                    exit(1)

                sleep(0.5)  # Check regularly
        except KeyboardInterrupt:
            error("Received Ctrl+C. Exiting...")
            subscriber_process.terminate()
            haproxy_server_checker_process.terminate()
            exit(1)
