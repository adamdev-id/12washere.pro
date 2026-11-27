"""Read the public data used by Saweria's donation widgets."""

import json
import math
import sys
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

STREAM_KEY = "ab95bc4c3d7dbed563380562e69c7861"


def read_widget(path, **params):
    query = urlencode({"stream_key": STREAM_KEY, **params})
    request = Request(
        f"https://backend.saweria.co/{path}?{query}",
        headers={"Accept": "application/json", "User-Agent": "12washere.pro-donation-status/1.0 (+https://12washere.pro/donation.html)"},
    )
    for attempt in range(3):
        try:
            with urlopen(request, timeout=15) as response:
                return json.load(response)["data"]
        except HTTPError as error:
            if error.code not in {429, 502, 503, 504} or attempt == 2:
                raise
            delay = 15 * (attempt + 1)
            retry_after = error.headers.get("Retry-After")
            if retry_after:
                try:
                    delay = max(delay, int(retry_after))
                except ValueError:
                    delay = max(delay, (parsedate_to_datetime(retry_after) - datetime.now(timezone.utc)).total_seconds())
            # Do not retry early when the provider requests a long pause.
            if delay > 120:
                raise
            print(f"Saweria returned HTTP {error.code}; retrying after {delay:.0f}s.", flush=True)
            time.sleep(delay)


def amount(value):
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise ValueError("Invalid donation amount")
    return result


def board(items, template):
    return {
        "title": str(template.get("text1", ""))[:300],
        "noAmount": bool(template.get("no_amount", False)),
        "items": [
            {"donator": str(item["donator"])[:100],
             "id": str(item.get("id", "")),
             "isUser": bool(item.get("is_user", False)),
             "amount": amount(item["amount"]),
             "currency": str(item.get("currency", "IDR"))[:3]}
            for item in items[:100]
        ],
    }


def query_donations():
    recent_template = read_widget("template/running_text")
    milestone = read_widget("template/milestone")
    leaderboard = read_widget("template/leaderboard")
    mode = leaderboard.get("mode", "all")
    if mode not in {"all", "month", "week", "day", "custom"}:
        raise ValueError("Unsupported Saweria leaderboard mode")
    params = {}
    if leaderboard.get("start_datetime"):
        params["start"] = datetime.strptime(leaderboard["start_datetime"], "%d-%m-%Y").strftime("%Y-%m-%d")
    progress = read_widget("widgets/milestone-progress", start_date=milestone["start_datetime"])
    return {
        "checkedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "recent": board(read_widget("widgets/recent"), recent_template),
        "goal": {"title": str(milestone.get("text1", ""))[:300],
                 "startDate": datetime.strptime(milestone["start_datetime"], "%d-%m-%Y").date().isoformat(),
                 "target": amount(milestone["target"]),
                 "progress": amount(progress["progress"]),
                 "currency": str(progress.get("currency", "IDR"))[:3]},
        "leaderboard": board(read_widget(f"widgets/leaderboard/{mode}", **params), leaderboard),
        "leaderboardPeriod": {"mode": mode, "startDate": params.get("start")},
    }


if __name__ == "__main__":
    snapshot = query_donations()
    Path(sys.argv[1]).write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Updated public donation snapshot.")
