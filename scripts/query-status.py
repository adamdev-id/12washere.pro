"""Write the public player roster reported by the server's Steam A2S endpoint."""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile

import a2s


ADDRESS = (os.environ.get("PZ_QUERY_HOST", "pz.12washere.pro"), int(os.environ.get("PZ_QUERY_PORT", "7449")))


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


def write_snapshot(path, status):
    """Publish a complete JSON file without exposing a partial write to Caddy."""
    destination = Path(path)
    temporary = None
    try:
        with NamedTemporaryFile(mode="w", encoding="utf-8", dir=destination.parent,
                                prefix=f".{destination.name}.", delete=False) as output:
            temporary = Path(output.name)
            json.dump(status, output, ensure_ascii=False)
            output.write("\n")
        os.chmod(temporary, 0o644)
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    status = query_server()
    status["checkedAt"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    write_snapshot(sys.argv[1], status)
    print(f"Steam query: {status['state']}; {status.get('playerCount', 0)} online")
