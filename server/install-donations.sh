#!/bin/sh
# Run as root from the staged donation-service deployment directory.
set -eu
stage=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
code=/opt/12washere-donations

if ! id 12washere-donations >/dev/null 2>&1; then
    useradd --system --user-group --no-create-home --shell /usr/sbin/nologin 12washere-donations
fi
install -d -m 755 "$code"
install -m 644 "$stage/donation-service.py" "$code/donation-service.py"
install -m 644 "$stage/donation-status.json" "$code/donation-status.json"
install -m 644 "$stage/12washere-donations.service" /etc/systemd/system/12washere-donations.service
install -m 644 "$stage/12washere-donations.caddy" /etc/caddy/12washere-donations.caddy
if [ ! -f /etc/12washere-donations.env ]; then
    install -m 600 "$stage/donations.env" /etc/12washere-donations.env
fi

cp -p /etc/caddy/Caddyfile "/etc/caddy/Caddyfile.donation-backup-$(date -u +%Y%m%dT%H%M%SZ)"
python3 - <<'PY'
from pathlib import Path
path = Path('/etc/caddy/Caddyfile')
text = path.read_text()
directive = '    import /etc/caddy/12washere-donations.caddy\n'
if directive.strip() not in text:
    marker = 'pz.12washere.pro {\n'
    if text.count(marker) != 1:
        raise SystemExit('Expected exactly one pz.12washere.pro site block')
    path.write_text(text.replace(marker, marker + directive, 1))
PY
caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
systemctl daemon-reload
systemctl enable 12washere-donations.service
systemctl restart 12washere-donations.service
systemctl reload caddy
systemctl is-active 12washere-donations.service caddy
