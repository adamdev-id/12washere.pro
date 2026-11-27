#!/bin/sh
# Run as root from the staged player-status deployment directory.
set -eu
stage=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
code=/opt/12washere-server-status

if ! id 12washere-status >/dev/null 2>&1; then
    useradd --system --user-group --no-create-home --shell /usr/sbin/nologin 12washere-status
fi
install -d -m 755 "$code"
install -m 644 "$stage/query-status.py" "$code/query-status.py"
install -m 644 "$stage/requirements-status.txt" "$code/requirements-status.txt"
if [ ! -x "$code/venv/bin/pip" ]; then
    python3 -m venv "$code/venv"
fi
"$code/venv/bin/pip" install --disable-pip-version-check --require-hashes --only-binary=:all: -r "$code/requirements-status.txt"
install -m 644 "$stage/12washere-server-status.service" /etc/systemd/system/12washere-server-status.service
install -m 644 "$stage/12washere-server-status.timer" /etc/systemd/system/12washere-server-status.timer
install -m 644 "$stage/12washere-server-status.caddy" /etc/caddy/12washere-server-status.caddy

backup="/etc/caddy/Caddyfile.player-status-backup-$(date -u +%Y%m%dT%H%M%SZ)"
cp -p /etc/caddy/Caddyfile "$backup"
python3 - <<'PY'
from pathlib import Path
path = Path('/etc/caddy/Caddyfile')
text = path.read_text()
directive = '    import /etc/caddy/12washere-server-status.caddy\n'
if directive.strip() not in text:
    marker = 'pz.12washere.pro {\n'
    if text.count(marker) != 1:
        raise SystemExit('Expected exactly one pz.12washere.pro site block')
    path.write_text(text.replace(marker, marker + directive, 1))
PY
if ! caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile; then
    cp -p "$backup" /etc/caddy/Caddyfile
    exit 1
fi
systemctl daemon-reload
systemctl start 12washere-server-status.service
systemctl enable --now 12washere-server-status.timer
systemctl reload caddy
systemctl is-active 12washere-server-status.timer caddy
