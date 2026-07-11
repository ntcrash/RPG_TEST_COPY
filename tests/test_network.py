"""Tests for the multiplayer client/server layer (roadmap P6 #40).

Two groups:
  * pure protocol tests (encode/decode + stream reassembly), no sockets;
  * loopback integration tests that spin up a real ``GameServer`` on an
    ephemeral 127.0.0.1 port and drive one or two ``NetworkClient``s through
    join / state-sync / chat / leave.

Everything is standard-library only and headless — no pygame, arcade, or
display — so it runs anywhere the rest of the suite does.
"""

import time
import unittest

from Code.game_server import GameServer
from Code.network_client import NetworkClient
from Code.network_protocol import (
    MAX_FRAME_BYTES,
    PROTOCOL_VERSION,
    FrameDecoder,
    MsgType,
    ProtocolError,
    decode_body,
    encode_message,
)


def _wait_until(predicate, timeout=3.0, interval=0.01):
    """Poll ``predicate`` until true or timeout. Returns its final truthiness."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return predicate()


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------

class ProtocolTests(unittest.TestCase):
    def test_encode_decode_roundtrip(self):
        frame = encode_message(MsgType.STATE, {"x": 1, "y": 2, "level": 3})
        # header (4 bytes) + body
        self.assertGreater(len(frame), 4)
        msg_type, payload = next(FrameDecoder().feed(frame))
        self.assertEqual(msg_type, MsgType.STATE)
        self.assertEqual(payload, {"x": 1, "y": 2, "level": 3})

    def test_default_payload_is_empty_object(self):
        msg_type, payload = decode_body(encode_message(MsgType.PING)[4:])
        self.assertEqual(msg_type, MsgType.PING)
        self.assertEqual(payload, {})

    def test_encode_rejects_unknown_type(self):
        with self.assertRaises(ProtocolError):
            encode_message("not_a_real_type", {})

    def test_encode_rejects_unserializable_payload(self):
        with self.assertRaises(ProtocolError):
            encode_message(MsgType.STATE, {"bad": {1, 2, 3}})  # set isn't JSON

    def test_decode_rejects_bad_json(self):
        with self.assertRaises(ProtocolError):
            decode_body(b"{not json")

    def test_decode_rejects_missing_type(self):
        with self.assertRaises(ProtocolError):
            decode_body(b'{"payload": {}}')

    def test_decode_rejects_non_object_payload(self):
        with self.assertRaises(ProtocolError):
            decode_body(b'{"type": "state", "payload": [1,2,3]}')

    def test_frame_length_cap_enforced(self):
        # Forge a header claiming an absurd length; decoder must refuse.
        import struct

        bogus = struct.pack(">I", MAX_FRAME_BYTES + 1) + b"x"
        with self.assertRaises(ProtocolError):
            list(FrameDecoder().feed(bogus))


class FrameDecoderTests(unittest.TestCase):
    def test_multiple_frames_in_one_chunk(self):
        blob = (
            encode_message(MsgType.PING, {"t": 1})
            + encode_message(MsgType.PING, {"t": 2})
            + encode_message(MsgType.PING, {"t": 3})
        )
        got = [p["t"] for _, p in FrameDecoder().feed(blob)]
        self.assertEqual(got, [1, 2, 3])

    def test_fragmented_frame_reassembled(self):
        frame = encode_message(MsgType.CHAT, {"text": "hello world"})
        dec = FrameDecoder()
        # Feed one byte at a time; only the final byte should complete it.
        results = []
        for i in range(len(frame)):
            results.extend(dec.feed(frame[i : i + 1]))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], MsgType.CHAT)
        self.assertEqual(results[0][1]["text"], "hello world")

    def test_partial_header_buffered(self):
        frame = encode_message(MsgType.PING, {"t": 9})
        dec = FrameDecoder()
        self.assertEqual(list(dec.feed(frame[:2])), [])  # < header length
        self.assertEqual(dec.pending_bytes, 2)
        out = list(dec.feed(frame[2:]))
        self.assertEqual(len(out), 1)
        self.assertEqual(dec.pending_bytes, 0)

    def test_trailing_partial_kept_after_full_frame(self):
        two = encode_message(MsgType.PING, {"t": 1}) + encode_message(MsgType.PING, {"t": 2})
        cut = len(encode_message(MsgType.PING, {"t": 1})) + 3  # first frame + 3 bytes
        dec = FrameDecoder()
        first = list(dec.feed(two[:cut]))
        self.assertEqual(len(first), 1)
        self.assertGreater(dec.pending_bytes, 0)
        second = list(dec.feed(two[cut:]))
        self.assertEqual(len(second), 1)
        self.assertEqual(second[0][1]["t"], 2)


# ---------------------------------------------------------------------------
# Server lifecycle
# ---------------------------------------------------------------------------

class ServerLifecycleTests(unittest.TestCase):
    def test_start_binds_ephemeral_port_and_stops(self):
        server = GameServer(host="127.0.0.1", port=0)
        port = server.start()
        try:
            self.assertGreater(port, 0)
            self.assertEqual(server.actual_port, port)
            self.assertEqual(server.player_count, 0)
        finally:
            server.stop()

    def test_double_start_raises(self):
        server = GameServer(host="127.0.0.1", port=0)
        server.start()
        try:
            with self.assertRaises(RuntimeError):
                server.start()
        finally:
            server.stop()


# ---------------------------------------------------------------------------
# Client <-> server integration (loopback)
# ---------------------------------------------------------------------------

class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.server = GameServer(host="127.0.0.1", port=0)
        self.port = self.server.start()
        self._clients = []

    def tearDown(self):
        for c in self._clients:
            try:
                c.disconnect()
            except OSError:
                pass
        self.server.stop()

    def _client(self, name):
        c = NetworkClient(host="127.0.0.1", port=self.port, name=name)
        self._clients.append(c)
        return c

    def test_single_client_join(self):
        c = self._client("Joe")
        self.assertTrue(c.connect(timeout=3.0))
        self.assertIsNotNone(c.player_id)
        self.assertTrue(_wait_until(lambda: self.server.player_count == 1))

    def test_protocol_mismatch_rejected(self):
        # Manually forge a JOIN with a wrong protocol version.
        import socket

        from Code.network_protocol import FrameDecoder, encode_message

        sock = socket.create_connection(("127.0.0.1", self.port), timeout=3.0)
        try:
            sock.sendall(encode_message(MsgType.JOIN, {"name": "X", "protocol": PROTOCOL_VERSION + 99}))
            dec = FrameDecoder()
            data = sock.recv(4096)
            msgs = list(dec.feed(data))
            self.assertTrue(any(m[0] == MsgType.JOIN_REJECT for m in msgs))
        finally:
            sock.close()

    def test_state_syncs_between_two_clients(self):
        a = self._client("Alice")
        b = self._client("Bob")
        self.assertTrue(a.connect(timeout=3.0))
        self.assertTrue(b.connect(timeout=3.0))
        self.assertTrue(_wait_until(lambda: self.server.player_count == 2))

        a.send_state({"x": 42, "y": 7, "level": 2})
        # Bob should see Alice's state land in his remote mirror.
        self.assertTrue(
            _wait_until(
                lambda: any(
                    info["state"].get("x") == 42 for info in b.remote_players().values()
                )
            )
        )
        seen = [info for info in b.remote_players().values() if info["state"].get("x") == 42]
        self.assertEqual(seen[0]["name"], "Alice")
        self.assertEqual(seen[0]["state"]["level"], 2)

    def test_new_client_receives_existing_players_in_ack(self):
        a = self._client("Alice")
        self.assertTrue(a.connect(timeout=3.0))
        a.send_state({"x": 100})
        self.assertTrue(_wait_until(lambda: self.server.player_count == 1))
        time.sleep(0.1)  # let the state settle server-side

        b = self._client("Bob")
        self.assertTrue(b.connect(timeout=3.0))
        # Bob's join_ack should already list Alice.
        self.assertTrue(
            _wait_until(lambda: any(i["name"] == "Alice" for i in b.remote_players().values()))
        )

    def test_leave_removes_player_for_others(self):
        a = self._client("Alice")
        b = self._client("Bob")
        self.assertTrue(a.connect(timeout=3.0))
        self.assertTrue(b.connect(timeout=3.0))
        self.assertTrue(_wait_until(lambda: self.server.player_count == 2))
        self.assertTrue(_wait_until(lambda: len(b.remote_players()) == 1))

        a.disconnect()
        self.assertTrue(_wait_until(lambda: self.server.player_count == 1))
        self.assertTrue(_wait_until(lambda: len(b.remote_players()) == 0))

    def test_chat_broadcast_via_callback(self):
        received = []
        a = self._client("Alice")
        b = NetworkClient(
            host="127.0.0.1",
            port=self.port,
            name="Bob",
            on_event=lambda t, p: received.append((t, p)) if t == MsgType.CHAT_BROADCAST else None,
        )
        self._clients.append(b)
        self.assertTrue(a.connect(timeout=3.0))
        self.assertTrue(b.connect(timeout=3.0))
        self.assertTrue(_wait_until(lambda: self.server.player_count == 2))

        a.send_chat("hello team")
        self.assertTrue(_wait_until(lambda: len(received) >= 1))
        self.assertEqual(received[0][1]["text"], "hello team")
        self.assertEqual(received[0][1]["name"], "Alice")

    def test_ping_pong(self):
        pongs = []
        c = NetworkClient(
            host="127.0.0.1",
            port=self.port,
            name="Joe",
            on_event=lambda t, p: pongs.append(p) if t == MsgType.PONG else None,
        )
        self._clients.append(c)
        self.assertTrue(c.connect(timeout=3.0))
        c.ping(token="abc")
        self.assertTrue(_wait_until(lambda: len(pongs) >= 1))
        self.assertEqual(pongs[0]["t"], "abc")


# ---------------------------------------------------------------------------
# High-level session helper
# ---------------------------------------------------------------------------

class MultiplayerSessionTests(unittest.TestCase):
    def test_session_from_env_disabled_by_default(self):
        from Code.multiplayer import session_from_env

        self.assertIsNone(session_from_env(env={}))
        self.assertIsNone(session_from_env(env={"MEGITECH_MULTIPLAYER": "0"}))

    def test_session_from_env_enabled(self):
        from Code.multiplayer import session_from_env

        s = session_from_env(
            env={
                "MEGITECH_MULTIPLAYER": "1",
                "MEGITECH_SERVER": "example.com:51000",
                "MEGITECH_PLAYER_NAME": "Skippy",
            }
        )
        self.assertIsNotNone(s)
        self.assertEqual(s.host, "example.com")
        self.assertEqual(s.port, 51000)
        self.assertEqual(s.name, "Skippy")

    def test_parse_server_address(self):
        from Code.multiplayer import parse_server_address

        self.assertEqual(parse_server_address("1.2.3.4:5000"), ("1.2.3.4", 5000))
        self.assertEqual(parse_server_address("host-only")[0], "host-only")
        # empty -> defaults; bad port -> default port
        host, port = parse_server_address("")
        self.assertTrue(host and port)
        self.assertEqual(parse_server_address("h:notaport")[0], "h")

    def test_start_returns_false_when_server_absent(self):
        # Nothing listening on this port -> graceful False, no exception.
        from Code.multiplayer import MultiplayerSession

        s = MultiplayerSession(host="127.0.0.1", port=1, name="Joe")
        self.assertFalse(s.start(timeout=1.0))
        self.assertIsNotNone(s.last_error)

    def test_session_end_to_end(self):
        from Code.multiplayer import MultiplayerSession

        server = GameServer(host="127.0.0.1", port=0)
        port = server.start()
        try:
            s1 = MultiplayerSession(host="127.0.0.1", port=port, name="One")
            s2 = MultiplayerSession(host="127.0.0.1", port=port, name="Two")
            self.assertTrue(s1.start(timeout=3.0))
            self.assertTrue(s2.start(timeout=3.0))
            self.assertTrue(_wait_until(lambda: server.player_count == 2))
            s1.publish(x=5, y=6, level=1)
            self.assertTrue(
                _wait_until(
                    lambda: any(i["state"].get("x") == 5 for i in s2.others().values())
                )
            )
            s1.stop()
            s2.stop()
        finally:
            server.stop()


if __name__ == "__main__":
    unittest.main(verbosity=2)
