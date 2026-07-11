"""High-level, opt-in multiplayer session helper for Magitech RPG (P6 #40).

Ties the low-level :class:`Code.network_client.NetworkClient` to the game in a
form the Arcade client can poll each frame *without knowing any wire details*.
It is deliberately display-free and **opt-in**: multiplayer only activates when
the player asks for it (env vars below or an explicit constructor). The
single-player default path never constructs a session, so single-player is
unchanged.

Opt-in via environment (read by :func:`session_from_env`):
    ``MEGITECH_MULTIPLAYER=1``   enable multiplayer
    ``MEGITECH_SERVER=host:port`` server address (default 127.0.0.1:50007)
    ``MEGITECH_PLAYER_NAME=...``  display name (default "Adventurer")

Typical game-side use (a future rendering step, not wired in yet)::

    session = session_from_env()
    if session and session.start():
        ...
        session.publish(x=player.x, y=player.y, level=1, hp=100)
        for pid, info in session.others().items():
            draw_remote_player(info["state"])
        ...
        session.stop()
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from Code.network_client import NetworkClient
from Code.network_protocol import DEFAULT_HOST, DEFAULT_PORT


class MultiplayerSession:
    """Convenience façade over a :class:`NetworkClient` for the game loop."""

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        name: str = "Adventurer",
    ) -> None:
        self.host = host
        self.port = port
        self.name = name
        self._client: Optional[NetworkClient] = None
        self.active = False
        self.last_error: Optional[str] = None

    def start(self, timeout: float = 5.0) -> bool:
        """Connect and join. Returns ``True`` if the session is live.

        Connection failures are swallowed into :attr:`last_error` and return
        ``False`` — a failed multiplayer connect must never crash the game;
        the caller simply continues in single-player.
        """
        client = NetworkClient(host=self.host, port=self.port, name=self.name)
        try:
            joined = client.connect(timeout=timeout)
        except OSError as exc:
            self.last_error = f"could not reach server: {exc}"
            return False
        if not joined:
            self.last_error = client.join_error or "join timed out"
            return False
        self._client = client
        self.active = True
        return True

    def publish(self, **state: Any) -> None:
        """Send this player's current state (e.g. ``publish(x=1, y=2, level=1)``)."""
        if self._client is not None and self.active:
            self._client.send_state(dict(state))

    def chat(self, text: str) -> None:
        """Send a chat message to every connected player."""
        if self._client is not None and self.active:
            self._client.send_chat(text)

    def others(self) -> Dict[int, Dict[str, Any]]:
        """Snapshot of the other connected players' ``{name, state}``."""
        if self._client is None:
            return {}
        return self._client.remote_players()

    @property
    def player_id(self) -> Optional[int]:
        return self._client.player_id if self._client else None

    def stop(self) -> None:
        """Leave the session and tear down the connection."""
        if self._client is not None:
            self._client.disconnect()
        self._client = None
        self.active = False


def parse_server_address(value: str, default_port: int = DEFAULT_PORT) -> tuple[str, int]:
    """Parse ``"host"`` or ``"host:port"`` into ``(host, port)``.

    A missing or unparseable port falls back to ``default_port``.
    """
    value = (value or "").strip()
    if not value:
        return DEFAULT_HOST, default_port
    if ":" in value:
        host, _, port_str = value.rpartition(":")
        host = host or DEFAULT_HOST
        try:
            return host, int(port_str)
        except ValueError:
            return host, default_port
    return value, default_port


def session_from_env(env: Optional[Dict[str, str]] = None) -> Optional[MultiplayerSession]:
    """Build a session from environment variables, or ``None`` if disabled.

    Returns a (not-yet-started) :class:`MultiplayerSession` only when
    ``MEGITECH_MULTIPLAYER`` is truthy; otherwise ``None`` so the caller stays
    in single-player. Pass ``env`` to test without touching ``os.environ``.
    """
    src = os.environ if env is None else env
    flag = str(src.get("MEGITECH_MULTIPLAYER", "")).strip().lower()
    if flag not in ("1", "true", "yes", "on"):
        return None
    host, port = parse_server_address(src.get("MEGITECH_SERVER", ""))
    name = str(src.get("MEGITECH_PLAYER_NAME", "Adventurer")).strip() or "Adventurer"
    return MultiplayerSession(host=host, port=port, name=name)
