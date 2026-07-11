"""Multiplayer client connector for Magitech RPG (roadmap P6 #40).

Wraps a TCP socket to a :class:`Code.game_server.GameServer`. It runs a
background receive thread that keeps a thread-safe mirror of every *other*
connected player's latest state, and exposes simple methods to push this
client's own state and chat.

This is transport only — it is **not** wired into the single-player game loop.
The existing Arcade client (`arcade_app.py`) is untouched; a future step polls
:meth:`remote_players` to draw other adventurers on the board. Because nothing
in the single-player path imports this module, single-player is unaffected.

Standard library only (``socket``/``threading``), so it imports and tests
headlessly.

Example::

    client = NetworkClient(host="127.0.0.1", port=50007, name="Joe")
    client.connect()
    client.send_state({"x": 100, "y": 200, "level": 1})
    others = client.remote_players()   # {player_id: {"name":..., "state":...}}
    client.disconnect()
"""

from __future__ import annotations

import socket
import threading
from typing import Any, Callable, Dict, Optional

from Code.network_protocol import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    PROTOCOL_VERSION,
    FrameDecoder,
    MsgType,
    ProtocolError,
    encode_message,
)

#: Signature of an optional event callback: ``cb(event_type, payload)``.
EventCallback = Callable[[str, Dict[str, Any]], None]


class NetworkClient:
    """A connection to the Magitech game server with a live remote-player mirror."""

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        name: str = "Adventurer",
        on_event: Optional[EventCallback] = None,
    ) -> None:
        self.host = host
        self.port = port
        self.name = name
        self._on_event = on_event

        self._sock: Optional[socket.socket] = None
        self._decoder = FrameDecoder()
        self._recv_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        self._running = False

        self.player_id: Optional[int] = None
        self.connected = False
        self._joined_event = threading.Event()
        self._join_error: Optional[str] = None
        #: {player_id: {"name": str, "state": dict}} for OTHER players.
        self._remote: Dict[int, Dict[str, Any]] = {}

    # -- lifecycle ---------------------------------------------------------

    def connect(self, timeout: float = 5.0) -> bool:
        """Open the socket, send JOIN, and block until the server acks.

        Returns ``True`` on a successful join, ``False`` if the server rejected
        the join or it timed out. Raises ``OSError`` if the TCP connect itself
        fails (host unreachable, refused, ...).
        """
        if self.connected:
            return True
        self._sock = socket.create_connection((self.host, self.port), timeout=timeout)
        self._sock.settimeout(None)
        self._running = True
        self._recv_thread = threading.Thread(
            target=self._recv_loop, name="MagitechNetClient", daemon=True
        )
        self._recv_thread.start()
        self._send(MsgType.JOIN, {"name": self.name, "protocol": PROTOCOL_VERSION})
        if not self._joined_event.wait(timeout):
            self.disconnect()
            return False
        return self.connected

    def disconnect(self) -> None:
        """Send a graceful LEAVE (best effort) and close the socket."""
        self._running = False
        if self._sock is not None:
            try:
                self._send(MsgType.LEAVE, {})
            except OSError:
                pass
            try:
                self._sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                self._sock.close()
            except OSError:
                pass
        self._sock = None
        self.connected = False

    # -- outbound ----------------------------------------------------------

    def send_state(self, state: Dict[str, Any]) -> None:
        """Publish this client's current state (position, level, hp, ...)."""
        self._send(MsgType.STATE, state)

    def send_chat(self, text: str) -> None:
        """Send a chat line to every connected player."""
        self._send(MsgType.CHAT, {"text": text})

    def ping(self, token: Any = None) -> None:
        """Send a ping; the server replies with a ``pong`` event."""
        self._send(MsgType.PING, {"t": token})

    def _send(self, msg_type: str, payload: Dict[str, Any]) -> None:
        if self._sock is None:
            raise OSError("not connected")
        data = encode_message(msg_type, payload)
        self._sock.sendall(data)

    # -- inbound -----------------------------------------------------------

    def remote_players(self) -> Dict[int, Dict[str, Any]]:
        """Thread-safe snapshot of every other player's ``{name, state}``."""
        with self._lock:
            return {pid: dict(info) for pid, info in self._remote.items()}

    def _recv_loop(self) -> None:
        while self._running and self._sock is not None:
            try:
                chunk = self._sock.recv(4096)
            except OSError:
                break
            if not chunk:
                break
            try:
                for msg_type, payload in self._decoder.feed(chunk):
                    self._handle(msg_type, payload)
            except ProtocolError:
                break
        self.connected = False
        # Unblock a caller still waiting in connect().
        self._joined_event.set()

    def _handle(self, msg_type: str, payload: Dict[str, Any]) -> None:
        if msg_type == MsgType.JOIN_ACK:
            self.player_id = payload.get("player_id")
            with self._lock:
                self._remote = {
                    int(pid): {"name": info.get("name", "?"), "state": info.get("state", {})}
                    for pid, info in payload.get("players", {}).items()
                }
            self.connected = True
            self._joined_event.set()
        elif msg_type == MsgType.JOIN_REJECT:
            self._join_error = payload.get("reason")
            self.connected = False
            self._joined_event.set()
        elif msg_type == MsgType.PLAYER_JOINED:
            pid = payload.get("player_id")
            with self._lock:
                self._remote[int(pid)] = {
                    "name": payload.get("name", "?"),
                    "state": payload.get("state", {}),
                }
        elif msg_type == MsgType.PLAYER_STATE:
            pid = payload.get("player_id")
            with self._lock:
                entry = self._remote.setdefault(int(pid), {"name": "?", "state": {}})
                entry["state"] = payload.get("state", {})
        elif msg_type == MsgType.PLAYER_LEFT:
            pid = payload.get("player_id")
            with self._lock:
                self._remote.pop(int(pid), None)
        # Fire the user callback for every event (chat, pong, errors, presence).
        if self._on_event is not None:
            try:
                self._on_event(msg_type, payload)
            except Exception:  # never let a client callback kill the recv loop
                pass

    @property
    def join_error(self) -> Optional[str]:
        """Reason string if the last join was rejected, else ``None``."""
        return self._join_error
