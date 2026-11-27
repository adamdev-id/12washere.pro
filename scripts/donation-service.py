"""Serve public donation totals and accept Saweria's signed HTTP callbacks.

Run behind the existing Caddy HTTPS proxy. Donor email and message are never
stored or returned. The private callback URL token is separate from the widget
key, because the widget URLs are public.
"""

import argparse
import copy
import hashlib
import hmac
import json
import os
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

STATUS_PATH = "/api/donations/status"
CALLBACK_PREFIX = "/api/donations/webhook/"
ALLOWED_ORIGINS = {"https://12washere.pro", "https://www.12washere.pro"}
TEST_ID = "00000000-0000-0000-0000-000000000000"


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def timestamp(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("A timezone is required")
    return parsed.astimezone(timezone.utc)


def verify(payload, signature, key):
    if not isinstance(payload, dict) or not re.fullmatch(r"[a-fA-F0-9]{64}", signature):
        return False
    fields = ("version", "id", "amount_raw", "donator_name", "donator_email")
    if any(field not in payload for field in fields):
        return False
    message = "".join(str(payload[field]) for field in fields).encode("utf-8")
    expected = hmac.new(key.encode("utf-8"), message, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature.lower())


class Store:
    def __init__(self, path, seed):
        self.path = str(path)
        with self.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY CHECK (id = 1), data TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS deliveries (id TEXT PRIMARY KEY, received_at TEXT NOT NULL)")
            if not db.execute("SELECT 1 FROM state WHERE id = 1").fetchone():
                document = copy.deepcopy(seed)
                timestamp(document["checkedAt"])
                document["updatedAt"] = document["checkedAt"]
                document["webhookConnected"] = False
                db.execute("INSERT INTO state VALUES (1, ?)", (json.dumps(document),))
                for item in document["recent"]["items"]:
                    if item.get("id"):
                        db.execute("INSERT OR IGNORE INTO deliveries VALUES (?, ?)", (item["id"], now()))

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        try:
            with db:
                yield db
        finally:
            db.close()

    def snapshot(self):
        with self.connect() as db:
            data = json.loads(db.execute("SELECT data FROM state WHERE id = 1").fetchone()[0])
        data["source"] = "saweria-webhook"
        data["checkedAt"] = now()
        # Callback IDs are only needed for server-side deduplication.
        for board in (data["recent"], data["leaderboard"]):
            for item in board["items"]:
                item.pop("id", None)
        return data

    def receive(self, payload):
        event_id = payload["id"]
        amount = payload["amount_raw"]
        name = payload["donator_name"]
        if not isinstance(event_id, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{1,100}", event_id):
            raise ValueError("Invalid donation ID")
        if type(amount) is not int or not 0 <= amount <= 10**12:
            raise ValueError("Invalid donation amount")
        if not isinstance(name, str) or not name.strip() or len(name) > 100:
            raise ValueError("Invalid donor name")
        created = timestamp(payload["created_at"])
        if (created - datetime.now(timezone.utc)).total_seconds() > 300:
            raise ValueError("Donation time is in the future")
        event_type = payload.get("type", "donation")
        if event_type not in {"donation", "test"}:
            raise ValueError("Unsupported callback type")
        is_test = event_id == TEST_ID or event_type == "test"
        received = now()
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            data = json.loads(db.execute("SELECT data FROM state WHERE id = 1").fetchone()[0])
            data["webhookConnected"] = True
            data["lastCallbackAt"] = received
            duplicate = db.execute("SELECT 1 FROM deliveries WHERE id = ?", (event_id,)).fetchone() is not None
            if not duplicate and not is_test:
                currency = data["goal"].get("currency", "IDR")
                item = {"id": event_id, "donator": name, "amount": amount,
                        "currency": currency, "isUser": bool(payload.get("donator_is_user", False)),
                        "createdAt": created.isoformat(timespec="seconds")}
                # Public widgets use the donation amount, not the post-fee balance.
                # Only signed fields determine the amount; unsigned 'cut' and 'etc'
                # fields cannot change public totals.
                recent = data["recent"]["items"]
                recent.append(item)
                recent.sort(key=lambda donor: donor.get("createdAt", ""), reverse=True)
                data["recent"]["items"] = recent[:5]
                if self.in_period(data.get("leaderboardPeriod", {}), created):
                    leaders = data["leaderboard"]["items"]
                    match = next((donor for donor in leaders if donor["donator"] == name
                                  and donor.get("currency", "IDR") == currency
                                  and bool(donor.get("isUser", False)) == item["isUser"]), None)
                    if match is None:
                        leaders.append({key: item[key] for key in ("donator", "amount", "currency", "isUser")})
                    else:
                        match["amount"] += amount
                    leaders.sort(key=lambda donor: (-donor["amount"], donor["donator"].casefold()))
                start = data["goal"].get("startDate", "0001-01-01")
                if created.date().isoformat() >= start:
                    data["goal"]["progress"] += amount
                data["updatedAt"] = received
                db.execute("INSERT INTO deliveries VALUES (?, ?)", (event_id, received))
            db.execute("UPDATE state SET data = ? WHERE id = 1", (json.dumps(data),))
        return {"received": True, "duplicate": duplicate, "test": is_test}

    @staticmethod
    def in_period(period, created):
        mode = period.get("mode", "all")
        if mode == "all":
            return True
        # The current site's leaderboard is all-time. Avoid silently mixing
        # rolling periods into its imported baseline.
        if mode == "custom" and period.get("startDate"):
            return created.date().isoformat() >= period["startDate"]
        raise ValueError("Reimport an all-time or custom leaderboard before enabling callbacks")


def handler_for(store, stream_key, callback_token):
    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(10)

        def log_message(self, format, *args):
            # Never write the private callback URL or request body into logs.
            pass

        def reply(self, status, data, body=True):
            encoded = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Vary", "Origin")
            if self.path.split("?", 1)[0] == STATUS_PATH and self.headers.get("Origin") in ALLOWED_ORIGINS:
                self.send_header("Access-Control-Allow-Origin", self.headers["Origin"])
                self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
            self.end_headers()
            if body:
                self.wfile.write(encoded)

        def do_GET(self):
            if self.path.split("?", 1)[0] != STATUS_PATH:
                return self.reply(404, {"error": "Not found"})
            return self.reply(200, store.snapshot())

        def do_HEAD(self):
            if self.path.split("?", 1)[0] != STATUS_PATH:
                return self.reply(404, {"error": "Not found"}, body=False)
            return self.reply(200, store.snapshot(), body=False)

        def do_OPTIONS(self):
            return self.reply(200 if self.path == STATUS_PATH else 404, {})

        def do_POST(self):
            if not hmac.compare_digest(self.path, CALLBACK_PREFIX + callback_token):
                return self.reply(404, {"error": "Not found"})
            if self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
                return self.reply(415, {"error": "JSON required"})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 32768:
                    return self.reply(413, {"error": "Invalid request size"})
                payload = json.loads(self.rfile.read(length))
                if not verify(payload, self.headers.get("Saweria-Callback-Signature", ""), stream_key):
                    return self.reply(401, {"error": "Invalid signature"})
                result = store.receive(payload)
            except (ValueError, KeyError, TypeError, OverflowError):
                return self.reply(400, {"error": "Invalid donation callback"})
            except sqlite3.Error:
                return self.reply(503, {"error": "Donation store unavailable"})
            return self.reply(200, result)

    return Handler


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--seed", required=True)
    parser.add_argument("--port", type=int, default=8756)
    args = parser.parse_args()
    key = os.environ["SAWERIA_STREAM_KEY"]
    token = os.environ["SAWERIA_CALLBACK_TOKEN"]
    if not re.fullmatch(r"[a-f0-9]{64}", token):
        raise ValueError("A private 256-bit callback token is required")
    seed = json.loads(Path(args.seed).read_text(encoding="utf-8"))
    if seed.get("leaderboardPeriod", {}).get("mode", "all") not in {"all", "custom"}:
        raise ValueError("Use an all-time or custom leaderboard")
    store = Store(args.db, seed)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler_for(store, key, token))
    server.daemon_threads = True
    print(f"Donation callbacks listening on 127.0.0.1:{args.port}", flush=True)
    server.serve_forever()
