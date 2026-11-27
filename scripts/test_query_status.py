"""Verify player-query failures and atomic publication of public status."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("query_status", Path(__file__).with_name("query-status.py"))
query = importlib.util.module_from_spec(spec)
spec.loader.exec_module(query)


class QueryTests(unittest.TestCase):
    def test_online_roster_only_contains_reported_printable_names(self):
        with patch.object(query.a2s, "info", return_value=SimpleNamespace(player_count=2, max_players=14)), \
             patch.object(query.a2s, "players", return_value=[SimpleNamespace(name="  Zoe\n"), SimpleNamespace(name="Ada\x00")]):
            result = query.query_server()
        self.assertEqual(result, {"state": "online", "playerCount": 2, "maxPlayers": 14, "names": ["Ada", "Zoe"]})

    def test_empty_server_does_not_need_player_query(self):
        with patch.object(query.a2s, "info", return_value=SimpleNamespace(player_count=0, max_players=14)), \
             patch.object(query.a2s, "players") as players:
            result = query.query_server()
        players.assert_not_called()
        self.assertEqual(result["state"], "online")
        self.assertEqual(result["names"], [])

    def test_transient_info_failure_is_retried(self):
        with patch.object(query.a2s, "info", side_effect=[TimeoutError(), SimpleNamespace(player_count=0, max_players=14)]) as info:
            result = query.query_server()
        self.assertEqual(info.call_count, 2)
        self.assertEqual(result["state"], "online")

    def test_unreachable_server_never_reuses_old_online_counts(self):
        with patch.object(query.a2s, "info", side_effect=TimeoutError()):
            self.assertEqual(query.query_server(), {"state": "unreachable"})

    def test_unavailable_names_do_not_make_an_online_server_offline(self):
        with patch.object(query.a2s, "info", return_value=SimpleNamespace(player_count=1, max_players=14)), \
             patch.object(query.a2s, "players", side_effect=TimeoutError()):
            result = query.query_server()
        self.assertEqual(result["state"], "online")
        self.assertEqual(result["playerCount"], 1)
        self.assertEqual(result["names"], [])


class PublicationTests(unittest.TestCase):
    def test_readers_see_complete_old_or_new_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "status.json"
            old = {"state": "online", "checkedAt": "2026-11-27T12:28:39+00:00"}
            new = {"state": "unreachable", "checkedAt": "2026-11-28T00:00:00+00:00"}
            path.write_text(json.dumps(old))
            replace = query.os.replace

            def inspect_commit(source, destination):
                self.assertEqual(json.loads(path.read_text()), old)
                self.assertEqual(json.loads(Path(source).read_text()), new)
                self.assertEqual(Path(source).parent, path.parent)
                replace(source, destination)

            with patch.object(query.os, "replace", side_effect=inspect_commit):
                query.write_snapshot(path, new)
            self.assertEqual(json.loads(path.read_text()), new)
            self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_failed_publication_preserves_existing_snapshot_and_cleans_tempfile(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "status.json"
            path.write_text('{"state":"online"}')
            with patch.object(query.os, "replace", side_effect=OSError("disk failure")):
                with self.assertRaises(OSError):
                    query.write_snapshot(path, {"state": "unreachable"})
            self.assertEqual(path.read_text(), '{"state":"online"}')
            self.assertEqual(list(Path(directory).iterdir()), [path])


if __name__ == "__main__":
    unittest.main()
