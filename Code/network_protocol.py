"""Wire protocol for Magitech RPG multiplayer (roadmap P6 #40).

This module is the pure, dependency-free core of the client/server layer. It
defines the message vocabulary the server and clients exchange and a
length-prefixed JSON framing so a TCP byte stream can be split back into
discrete messages regardless of how the OS fragments it.

Design goals:
* **No game/GUI imports.** Only the Python standard library, so it imports and
  unit-tests headlessly (no pygame, no arcade, no display) and can never affect
  single-player.
* **Deterministic + testable.** Encoding/decoding are pure functions;
  ``FrameDecoder`` is a tiny state machine you can feed arbitrary byte chunks.

Framing
-------
Every message on the wire is::

    <4-byte big-endian unsigned length N> <N bytes of UTF-8 JSON>

The JSON body is an object ``{"type": <str>, "payload": <obj>}``. Length-prefix
framing is used (rather than newline delimiting) because payloads are arbitrary
JSON and TCP does not preserve message boundaries.
"""

from __future__ import annotations

import json
import struct
from typing import Any, Dict, Iterator, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Protocol revision. The server rejects clients whose PROTOCOL_VERSION differs
#: so an old client can't silently desync against a newer server.
PROTOCOL_VERSION = 1

#: Default TCP port for the game server. Picked from the IANA dynamic/private
#: range (49152-65535) to avoid colliding with common services.
DEFAULT_PORT = 50007

#: Default bind/connect host. Loopback by default; a real host must opt into
#: "0.0.0.0" (server) / a LAN IP (client) explicitly.
DEFAULT_HOST = "127.0.0.1"

#: Header is a single unsigned 32-bit big-endian length.
_HEADER = struct.Struct(">I")
_HEADER_LEN = _HEADER.size

#: Hard cap on a single frame (8 MiB) so a malformed/malicious length prefix
#: can't make a peer try to buffer unbounded memory.
MAX_FRAME_BYTES = 8 * 1024 * 1024


# ---------------------------------------------------------------------------
# Message types (client -> server, server -> client)
# ---------------------------------------------------------------------------

class MsgType:
    """String constants for every message ``type`` on the wire."""

    # client -> server
    JOIN = "join"                 # {name, protocol}
    STATE = "state"               # {x, y, level, hp, ...} a player's live state
    CHAT = "chat"                 # {text}
    LEAVE = "leave"               # {} graceful disconnect
    PING = "ping"                 # {t}

    # server -> client
    JOIN_ACK = "join_ack"         # {player_id, protocol, players: {...}}
    JOIN_REJECT = "join_reject"   # {reason}
    PLAYER_JOINED = "player_joined"   # {player_id, name, state}
    PLAYER_STATE = "player_state"     # {player_id, state}
    PLAYER_LEFT = "player_left"       # {player_id}
    CHAT_BROADCAST = "chat_broadcast"  # {player_id, name, text}
    PONG = "pong"                 # {t}
    ERROR = "error"               # {message}


#: Every valid type, for validation on decode.
_VALID_TYPES = frozenset(
    v for k, v in vars(MsgType).items() if not k.startswith("_") and isinstance(v, str)
)


class ProtocolError(Exception):
    """Raised when bytes on the wire can't be parsed as a valid frame."""


# ---------------------------------------------------------------------------
# Encode / decode
# ---------------------------------------------------------------------------

def encode_message(msg_type: str, payload: Dict[str, Any] | None = None) -> bytes:
    """Serialize ``(msg_type, payload)`` into a single length-prefixed frame.

    ``payload`` defaults to an empty object. The result is
    ``header(len) + json_bytes`` ready to write straight onto a socket.
    """
    if msg_type not in _VALID_TYPES:
        raise ProtocolError(f"unknown message type: {msg_type!r}")
    body = {"type": msg_type, "payload": {} if payload is None else payload}
    try:
        raw = json.dumps(body, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError) as exc:  # non-JSON-serializable payload
        raise ProtocolError(f"payload not JSON-serializable: {exc}") from exc
    if len(raw) > MAX_FRAME_BYTES:
        raise ProtocolError(f"frame too large: {len(raw)} bytes")
    return _HEADER.pack(len(raw)) + raw


def decode_body(raw: bytes) -> Tuple[str, Dict[str, Any]]:
    """Parse a single frame *body* (the JSON bytes, no header) into a tuple.

    Returns ``(msg_type, payload)``. Raises :class:`ProtocolError` on malformed
    JSON, a missing/invalid ``type``, or a non-object ``payload``.
    """
    try:
        obj = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise ProtocolError(f"invalid JSON body: {exc}") from exc
    if not isinstance(obj, dict):
        raise ProtocolError("frame body is not a JSON object")
    msg_type = obj.get("type")
    if msg_type not in _VALID_TYPES:
        raise ProtocolError(f"missing/unknown message type: {msg_type!r}")
    payload = obj.get("payload", {})
    if not isinstance(payload, dict):
        raise ProtocolError("payload is not a JSON object")
    return msg_type, payload


class FrameDecoder:
    """Reassembles a TCP byte stream into whole message frames.

    TCP delivers a stream, not messages: a single ``recv`` can return half a
    frame, one frame, or several frames plus a partial one. Feed every chunk to
    :meth:`feed` and iterate the ``(type, payload)`` tuples it yields once
    complete frames are available. Partial data is buffered until the rest
    arrives.
    """

    def __init__(self) -> None:
        self._buf = bytearray()

    def feed(self, data: bytes) -> Iterator[Tuple[str, Dict[str, Any]]]:
        """Add received bytes and yield every complete message now decodable."""
        if data:
            self._buf.extend(data)
        while True:
            if len(self._buf) < _HEADER_LEN:
                return
            (length,) = _HEADER.unpack_from(self._buf, 0)
            if length > MAX_FRAME_BYTES:
                raise ProtocolError(f"declared frame length too large: {length}")
            total = _HEADER_LEN + length
            if len(self._buf) < total:
                return  # frame not fully arrived yet
            body = bytes(self._buf[_HEADER_LEN:total])
            del self._buf[:total]
            yield decode_body(body)

    @property
    def pending_bytes(self) -> int:
        """Bytes buffered so far that don't yet form a complete frame."""
        return len(self._buf)
