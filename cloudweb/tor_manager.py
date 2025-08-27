import os
import shutil
import socket
import subprocess
from typing import Optional

from .paths import DATA_DIR


def is_port_open(host: str, port: int) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.2)
    try:
        return sock.connect_ex((host, port)) == 0
    finally:
        sock.close()


class TorManager:
    """Simple Tor process manager using system 'tor' binary.

    - Uses SOCKS at 127.0.0.1:9050
    - Creates a DataDirectory under app data folder
    - Starts tor only if port is not already open
    """

    def __init__(self, socks_host: str = '127.0.0.1', socks_port: int = 9050) -> None:
        self.socks_host = socks_host
        self.socks_port = socks_port
        self.process: Optional[subprocess.Popen] = None
        self.started_by_us = False
        self.tor_binary = shutil.which('tor')
        self.data_dir = os.path.join(DATA_DIR, 'tor_data')
        os.makedirs(self.data_dir, exist_ok=True)

    def start(self) -> bool:
        if is_port_open(self.socks_host, self.socks_port):
            return True
        if not self.tor_binary:
            return False
        cmd = [
            self.tor_binary,
            '--SOCKSPort', str(self.socks_port),
            '--DataDirectory', self.data_dir,
        ]
        try:
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            self.started_by_us = True
            return True
        except Exception:
            self.process = None
            self.started_by_us = False
            return False

    def stop(self) -> None:
        if self.process and self.started_by_us:
            try:
                self.process.terminate()
            except Exception:
                pass
            self.process = None
            self.started_by_us = False

