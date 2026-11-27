"""Read the public data used by Saweria's donation widgets."""

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

STREAM_KEY = "ab95bc4c3d7dbed563380562e69c7861"


def read_widget(path, **params):
    query = urlencode({"stream_key": STREAM_KEY, **params})
    with urlopen(f"https://backend.saweria.co/{path}?{query}", timeout=15) as response:
        return json.load(response)["data"]


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
                 "target": amount(milestone["target"]),
                 "progress": amount(progress["progress"]),
                 "currency": str(progress.get("currency", "IDR"))[:3]},
        "leaderboard": board(read_widget(f"widgets/leaderboard/{mode}", **params), leaderboard),
    }


if __name__ == "__main__":
    snapshot = query_donations()
    Path(sys.argv[1]).write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Updated public donation snapshot.")
