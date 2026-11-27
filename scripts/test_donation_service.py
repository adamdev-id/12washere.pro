"""Integrity checks for the public donation callback service."""

import hashlib
import hmac
import importlib.util
import json
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

spec = importlib.util.spec_from_file_location("donation_service", Path(__file__).with_name("donation-service.py"))
service = importlib.util.module_from_spec(spec)
spec.loader.exec_module(service)
KEY = "test-stream-key"
TOKEN = "a" * 64


def seed():
    return {
        "checkedAt": "2026-11-01T00:00:00+00:00",
        "recent": {"noAmount": False, "items": [{"id": "seed-id", "donator": "Alice", "amount": 10000, "currency": "IDR"}]},
        "goal": {"title": "Server costs", "target": 500000, "progress": 10000, "currency": "IDR", "startDate": "2024-02-01"},
        "leaderboard": {"title": "Donors", "noAmount": False, "items": [{"donator": "Alice", "amount": 10000, "currency": "IDR"}]},
        "leaderboardPeriod": {"mode": "all", "startDate": None},
    }


def donation(event_id="new-donation", name="Bob", amount=25000):
    return {"version": "2022.01", "created_at": service.now(), "id": event_id, "type": "donation",
            "amount_raw": amount, "cut": 1250, "donator_name": name, "donator_email": "private@example.com",
            "donator_is_user": False, "message": "PRIVATE MESSAGE"}


def signature(payload):
    values = (payload[field] for field in ("version", "id", "amount_raw", "donator_name", "donator_email"))
    return hmac.new(KEY.encode(), "".join(map(str, values)).encode(), hashlib.sha256).hexdigest()


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "donations.sqlite3"
        self.store = service.Store(self.path, seed())

    def tearDown(self):
        self.directory.cleanup()

    def test_all_sections_update_and_survive_restart(self):
        self.store.receive(donation())
        state = service.Store(self.path, seed()).snapshot()
        self.assertEqual(state["goal"]["progress"], 35000)
        self.assertEqual(state["recent"]["items"][0]["donator"], "Bob")
        self.assertEqual(state["leaderboard"]["items"][0]["amount"], 25000)
        self.assertTrue(state["webhookConnected"])

    def test_duplicate_delivery_and_imported_recent_id_never_double_count(self):
        self.store.receive(donation())
        self.assertTrue(self.store.receive(donation())["duplicate"])
        self.assertTrue(self.store.receive(donation("seed-id"))["duplicate"])
        self.assertEqual(self.store.snapshot()["goal"]["progress"], 35000)

    def test_concurrent_duplicate_delivery_is_atomic(self):
        with ThreadPoolExecutor(max_workers=8) as executor:
            list(executor.map(lambda _: self.store.receive(donation()), range(12)))
        self.assertEqual(self.store.snapshot()["goal"]["progress"], 35000)

    def test_existing_donor_aggregates_and_recent_list_is_limited(self):
        for i in range(8):
            self.store.receive(donation(f"donation-{i}", "Alice", 1000))
        state = self.store.snapshot()
        self.assertEqual(state["leaderboard"]["items"][0]["amount"], 18000)
        self.assertEqual(len(state["recent"]["items"]), 5)

    def test_test_callback_does_not_invent_a_donation(self):
        self.store.receive(donation(service.TEST_ID))
        state = self.store.snapshot()
        self.assertTrue(state["webhookConnected"])
        self.assertEqual(state["goal"]["progress"], 10000)
        self.assertEqual(len(state["recent"]["items"]), 1)

    def test_private_fields_and_unsigned_amount_override_are_not_used(self):
        payload = donation()
        payload["etc"] = {"amount_to_display": 999999999}
        self.store.receive(payload)
        state = self.store.snapshot()
        self.assertEqual(state["goal"]["progress"], 35000)
        for text in (json.dumps(state), self.path.read_bytes().decode("utf-8", errors="ignore")):
            self.assertNotIn("private@example.com", text)
            self.assertNotIn("PRIVATE MESSAGE", text)
        self.assertNotIn('"id"', json.dumps(state))

    def test_bad_amounts_and_dates_do_not_mutate_state(self):
        for change in ({"amount_raw": -1}, {"amount_raw": True}, {"amount_raw": "1000"},
                       {"amount_raw": 10**13}, {"created_at": "invalid"}, {"created_at": "2999-01-01T00:00:00Z"}):
            payload = donation()
            payload.update(change)
            with self.assertRaises((ValueError, TypeError)):
                self.store.receive(payload)
        self.assertEqual(self.store.snapshot()["goal"]["progress"], 10000)

    def test_goal_start_date_is_respected(self):
        payload = donation()
        payload["created_at"] = "2024-01-01T00:00:00Z"
        self.store.receive(payload)
        self.assertEqual(self.store.snapshot()["goal"]["progress"], 10000)


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.store = service.Store(Path(self.directory.name) / "state.sqlite3", seed())
        self.server = service.ThreadingHTTPServer(("127.0.0.1", 0), service.handler_for(self.store, KEY, TOKEN))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.origin = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.directory.cleanup()

    def request(self, path, payload=None, signature_value=None, origin=None):
        headers = {"Content-Type": "application/json"}
        if signature_value:
            headers["Saweria-Callback-Signature"] = signature_value
        if origin:
            headers["Origin"] = origin
        request = Request(self.origin + path, data=None if payload is None else json.dumps(payload).encode(), headers=headers)
        return urlopen(request, timeout=5)

    def test_signature_and_private_url_are_both_required(self):
        payload = donation()
        for path, sig, status in ((service.CALLBACK_PREFIX + "wrong", signature(payload), 404),
                                  (service.CALLBACK_PREFIX + TOKEN, "0" * 64, 401),
                                  (service.CALLBACK_PREFIX + TOKEN, None, 401)):
            with self.assertRaises(HTTPError) as caught:
                self.request(path, payload, sig)
            self.assertEqual(caught.exception.code, status)
            caught.exception.close()
        self.assertEqual(self.store.snapshot()["goal"]["progress"], 10000)
        with self.request(service.CALLBACK_PREFIX + TOKEN, payload, signature(payload)) as response:
            self.assertEqual(response.status, 200)
        self.assertEqual(self.store.snapshot()["goal"]["progress"], 35000)

    def test_public_data_has_cors_for_the_website_and_no_caching(self):
        with self.request(service.STATUS_PATH, origin="https://12washere.pro") as response:
            self.assertEqual(response.headers["Access-Control-Allow-Origin"], "https://12washere.pro")
            self.assertEqual(response.headers["Cache-Control"], "no-store")
            self.assertEqual(json.load(response)["source"], "saweria-webhook")
        with self.request(service.STATUS_PATH, origin="https://example.com") as response:
            self.assertIsNone(response.headers.get("Access-Control-Allow-Origin"))


if __name__ == "__main__":
    unittest.main()
