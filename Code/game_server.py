"""Authoritative-lite multiplayer game server for Magitech RPG (roadmap P6 #40).

The **new server component** of the client/server setup. It is a threaded TCP
server that lets several Magitech clients share a world view: each connected
player streams its own state (position, level, hp, ...) and the server relays
every player's state to everyone else, plus join/leave and chat notifications.

It is a *relay / presence* server, not a full physics authority — combat and
world logic still run client-side exactly as in single-player. That keeps the
addition strictly additive: **nothing here is imported by the single-player
game, so single-player behaviour cannot change.**

Dependency-free (standard library only: ``socket``, ``threading``,
``socketserver``), so it runs and unit-tests headlessly with no pygame/arcade
and no display.

Usage::

    server = GameServer(host="0.0.0.0", port=50007)
    server.start()          # spawns a background thread; returns immediately
    ...                     # server.actual_port is the bound port
    server.stop()

Or run ``python server_app.py`` for a standalone, blocking server process.
"""

from __future__ import annotations

import socketserver
import threading
from typing import Any, Dict, Optional

from Code.network_protocol import (
    PROTOCOL_VERSION,
    FrameDecoder,
    MsgType,
    ProtocolError,
    encode_message,
)


class _Player:
    """Server-side record of one connected client."""

    def __init__(self, player_id: int, name: str, handler: "_ClientHandler") -> None:
        self.player_id = player_id
        self.name = name
        self.handler = handler
        self.state: Dict[str, Any] = {}


class GameServer:
    """Threaded TCP presence/relay server for Magitech multiplayer.

    Thread-safety: all mutations of the shared ``_players`` registry go through
    ``_lock``. Each client is serviced by its own ``_ClientHandler`` thread
    (``ThreadingTCPServer``); broadcasts iterate a snapshot taken under the lock.
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 50007) -> None:
        self.host = host
        self.port = port
        self._server: Optional["_ThreadingServer"] = None
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        self._players: Dict[int, _Player] = {}
        self._next_id = 1

    # -- lifecycle ---------------------------------------------------------

    def start(self) -> int:
        """Bind, then serve in a background daemon thread. Returns the port.

        Passing ``port=0`` binds an ephemeral port (handy for tests); read the
        chosen port back from :attr:`actual_port` after ``start()``.
        """
        if self._server is not None:
            raise RuntimeError("server already started")
        self._server = _ThreadingServer((self.host, self.port), _ClientHandler)
        self._server.game_server = self
        self._thread = threading.Thread(
            target=self._server.serve_forever, name="MagitechGameServer", daemon=True
        )
        self._thread.start()
        return self.actual_port

    def stop(self) -> None:
        """Shut the server down and close every client connection."""
        if self._server is None:
            return
        self._server.shutdown()
        self._server.server_close()
        self._server = None
        with self._lock:
            self._players.clear()

    @property
    def actual_port(self) -> int:
        """The concrete port the listening socket is bound to."""
        if self._server is None:
            return self.port
        return self._server.server_address[1]

    @property
    def player_count(self) -> int:
        with self._lock:
            return len(self._players)

    def player_names(self) -> Dict[int, str]:
        """Snapshot of ``{player_id: name}`` for currently connected players."""
        with self._lock:
            return {pid: p.name for pid, p in self._players.items()}

    # -- registry (called from handler threads) ----------------------------

    def _register(self, name: str, handler: "_ClientHandler") -> _Player:
        with self._lock:
            player_id = self._next_id
            self._next_id += 1
            player = _Player(player_id, name, handler)
            self._players[player_id] = player
            # snapshot of the others' current state for the join ack
            others = {
                str(pid): {"name": p.name, "state": p.state}
                for pid, p in self._players.items()
                if pid != player_id
            }
        handler.send(
            MsgType.JOIN_ACK,
            {"player_id": player_id, "protocol": PROTOCOL_VERSION, "players": others},
        )
        self._broadcast(
            MsgType.PLAYER_JOINED,
            {"player_id": player_id, "name": name, "state": {}},
            exclude=player_id,
        )
        return player

    def _unregister(self, player_id: int) -> None:
        with self._lock:
            existed = self._players.pop(player_id, None)
        if existed is not None:
            self._broadcast(MsgType.PLAYER_LEFT, {"player_id": player_id})

    def _update_state(self, player_id: int, state: Dict[str, Any]) -> None:
        with self._lock:
            player = self._players.get(player_id)
            if player is None:
                return
            player.state = state
        self._broadcast(
            MsgType.PLAYER_STATE,
            {"player_id": player_id, "state": state},
            exclude=player_id,
        )

    def _relay_chat(self, player_id: int, text: str) -> None:
        with self._lock:
            player = self._players.get(player_id)
            name = player.name if player else "?"
        self._broadcast(
            MsgType.CHAT_BROADCAST,
            {"player_id": player_id, "name": name, "text": text},
        )

    def _broadcast(
        self, msg_type: str, payload: Dict[str, Any], exclude: Optional[int] = None
    ) -> None:
        with self._lock:
            targets = [p.handler for pid, p in self._players.items() if pid != exclude]
        for handler in targets:
            handler.send(msg_type, payload)


class _ThreadingServer(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True
    game_server: GameServer  # set by GameServer.start()


class _ClientHandler(socketserver.BaseRequestHandler):
    """Per-connection handler: reads framed messages and drives the server."""

    def setup(self) -> None:
        self._decoder = FrameDecoder()
        self._send_lock = threading.Lock()
        self._player_id: Optional[int] = None
        self._joined = False

    def send(self, msg_type: str, payload: Dict[str, Any]) -> None:
        """Frame + write a message to this client (best-effort, thread-safe)."""
        try:
            data = encode_message(msg_type, payload)
        except ProtocolError:
            return
        with self._send_lock:
            try:
                self.request.sendall(data)
            except OSError:
                pass  # peer gone; handle() loop will notice and clean up

    def handle(self) -> None:
        server: GameServer = self.server.game_server
        try:
            while True:
                try:
                    chunk = self.request.recv(4096)
                except OSError:
                    break
                if not chunk:
                    break
                try:
                    messages = list(self._decoder.feed(chunk))
                except ProtocolError:
                    self.send(MsgType.ERROR, {"message": "bad frame"})
                    break
                for msg_type, payload in messages:
                    if not self._dispatch(server, msg_type, payload):
                        return
        finally:
            if self._player_id is not None:
                server._unregister(self._player_id)

    def _dispatch(self, server: GameServer, msg_type: str, payload: Dict[str, Any]) -> bool:
        """Handle one message. Returns False to close the connection."""
        if not self._joined:
            if msg_type != MsgType.JOIN:
                self.send(MsgType.JOIN_REJECT, {"reason": "must join first"})
                return False
            if payload.get("protocol") != PROTOCOL_VERSION:
                self.send(MsgType.JOIN_REJECT, {"reason": "protocol version mismatch"})
                return False
            name = str(payload.get("name") or "Adventurer")[:32]
            player = server._register(name, self)
            self._player_id = player.player_id
            self._joined = True
            return True

        if msg_type == MsgType.STATE:
            server._update_state(self._player_id, payload)
        elif msg_type == MsgType.CHAT:
            text = str(payload.get("text", ""))[:500]
            if text:
                server._relay_chat(self._player_id, text)
        elif msg_type == MsgType.PING:
            self.send(MsgType.PONG, {"t": payload.get("t")})
        elif msg_type == MsgType.LEAVE:
            return False
        # unknown-but-valid types are ignored (forward compatibility)
        return True


def run_server(host: str = "0.0.0.0", port: int = 50007) -> None:
    """Start a server and block until Ctrl-C. Used by ``server_app.py``."""
    server = GameServer(host=host, port=port)
    bound = server.start()
    print(f"Magitech game server listening on {host}:{bound} (protocol v{PROTOCOL_VERSION})")
    print("Press Ctrl-C to stop.")
    try:
        while True:
            threading.Event().wait(3600)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        server.stop()
