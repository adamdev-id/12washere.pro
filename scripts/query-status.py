"""Write the public player roster reported by the server's Steam A2S endpoint."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import a2s


ADDRESS = ("pz.12washere.pro", 7449)


def query_server():
    for _ in range(2):
        try:
            info = a2s.info(ADDRESS, timeout=4.0)
            break
        except (OSError, a2s.BrokenMessageError, UnicodeError):
            continue
    else:
        return {"state": "unreachable"}

    names = []
    if info.player_count:
        try:
            for player in a2s.players(ADDRESS, timeout=4.0):
                name = "".join(char for char in player.name if char.isprintable()).strip()
                if name:
                    names.append(name[:80])
        except (OSError, a2s.BrokenMessageError, UnicodeError):
            pass

    return {
        "state": "online",
        "playerCount": info.player_count,
        "maxPlayers": info.max_players,
        "names": sorted(names, key=str.casefold)[:info.player_count],
    }


if __name__ == "__main__":
    status = query_server()
    status["checkedAt"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    Path(sys.argv[1]).write_text(json.dumps(status, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Steam query: {status['state']}; {status.get('playerCount', 0)} online")
