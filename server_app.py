"""Standalone Magitech multiplayer server launcher (roadmap P6 #40).

The server counterpart to the Arcade client entry point (``arcade_app.py``).
Run it on whatever machine should host a shared session::

    python server_app.py                 # bind 0.0.0.0:50007
    python server_app.py --port 51000     # custom port
    python server_app.py --host 127.0.0.1 # loopback only

Clients then connect by launching the game with, e.g.::

    MEGITECH_MULTIPLAYER=1 MEGITECH_SERVER=<host>:<port> python main.py

The server is standard-library only (no pygame/arcade needed) so it can run on a
headless box. Single-player is completely independent of this process.
"""

from __future__ import annotations

import argparse

from Code.game_server import run_server
from Code.network_protocol import DEFAULT_PORT


def main() -> None:
    parser = argparse.ArgumentParser(description="Magitech RPG multiplayer server")
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="interface to bind (default 0.0.0.0 = all; use 127.0.0.1 for loopback only)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"TCP port to listen on (default {DEFAULT_PORT})",
    )
    args = parser.parse_args()
    run_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
