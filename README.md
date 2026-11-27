# 12WASHERE — Project Zomboid landing page

## Windows client patcher

The standalone [12washere.pro Patcher](patcher/README.md) bundles the spawn-menu,
clothing-label and custom outfit preset fixes, plus the local Derpy Autodrive
Viewpoint route add-on. It detects Steam libraries,
blocks patch/restore while Project Zomboid is running, and keeps reversible
backups. Player files are in `downloads/`; there is no Workshop publication.
Players download the [standalone EXE](https://12washere.pro/downloads/12washere.pro-Patcher.exe)
from the [required setup section](https://12washere.pro/mods.html#client-patcher).
See [player instructions and limits](downloads/README.txt). The ZIPs are optional.
`.gitattributes` keeps the published executables, archives and hashed payload
files byte-for-byte intact.

[12washere.pro](https://12washere.pro/) is a static site published by GitHub Pages from the root of `main`. The custom domain is set in `CNAME` and the repository's Pages settings. No build step is required.

## Joining

In Project Zomboid, open **Join** and enter `pz.12washere.pro` as the hostname and `7449` as the port. The site copies the values shown next to each Copy button. The Steam link opens the game, where players finish joining.

The game hostname points to the separate Google Cloud server. Keep its game DNS record unproxied so players can reach the UDP game port. The landing page does not query or control the game server.

## Editing

- `index.html`: page copy and connection details. Update each displayed instance if the hostname or port changes; the Copy buttons read directly from the adjacent `<code>` element.
- `script.js`: Join dialog and clipboard controls. Increment the `?v=` on its URL in `index.html` when changing it so returning visitors fetch the new script.
- `style.css` and `assets/`: layout, colors, and SVG artwork. Google Fonts has local system-font fallbacks.
- `donation.html`, `donation.css`, and `donation.js`: donation page with recent donations first, separate Saweria and donation QR actions, the donation goal, and the leaderboard. The QR action opens a fading native dialog; without JavaScript it links directly to the donation page. The QR encodes `https://saweria.co/12washere`, uses the site's dark green and opaque cream colors, and retains a four-module quiet zone. The surrounding card carries the orange 12WASHERE branding without covering the QR. Visitors scan it with their phone camera, enter an amount on Saweria, and select QRIS there; this static link QR is not a banking-app payment QRIS. The popup also includes a direct donation button for visitors using the same phone. Donation page translations are in `language.js`.
- Donation updates use [Saweria's signed HTTP webhook](https://saweria.co/docs/webhook), received by `scripts/donation-service.py` on the existing Google Cloud server. The site polls `https://pz.12washere.pro/api/donations/status` every 30 seconds while visible, and immediately after reconnecting or returning to the tab. The local JSON is a fallback when the service is unreachable. Both browser CORS restrictions and Saweria's blocking of GitHub/cloud polling are avoided by receiving the official callbacks. The old GitHub donation polling workflow has been removed.
- `server/` contains the systemd service, Caddy route, and repeatable installer. The service listens only on `127.0.0.1:8756`, behind the existing HTTPS proxy; it does not restart or modify the game or control panel. Durable SQLite state lives in `/var/lib/12washere-donations/state.sqlite3`, outside the deployed code. It starts with `donation-status.json` once, adds confirmed donations to the goal and all-time leaderboard, keeps the five most recent donations, deduplicates callback IDs across restarts, and ignores Saweria's nil-UUID test notification. Donor emails and messages are used only for signature verification and are never persisted or returned.
- The Saweria dashboard must have HTTP Webhook enabled with the private callback URL. Its URL token and the signature key are stored only in root-readable `/etc/12washere-donations.env` as `SAWERIA_CALLBACK_TOKEN` and `SAWERIA_STREAM_KEY`. The private URL has the form `https://pz.12washere.pro/api/donations/webhook/<private-token>`; do not commit its token. Both the private URL and a valid Saweria signature are required. The status response reports `webhookConnected: false` until a verified callback arrives, and the page explicitly shows that setup is pending. Do not manually send fake donations to the production callback for testing.
- `python -B -m unittest discover -s scripts -p test_donation_service.py -v` checks signature verification, private URL protection, all three sections, persistence, duplicate/concurrent delivery, test callbacks, and public-data privacy. `python scripts/query-donations.py donation-status.json` imports the current public widget data from a permitted connection for the initial baseline. The current leaderboard is all-time; changes to the goal target or Saweria leaderboard settings require an explicit baseline/configuration update on the receiver.

Without JavaScript, the Join links go to the connection section, where players can copy the details manually.

## Player roster and modlist

- `mods.json` lists the configured Steam Workshop items, one card per Workshop ID. Update it from the server's `WorkshopItems=` list when that list changes. Each item has a primary `category` (see `categoryLabels` in `mods.js`) and a Steam Workshop `thumbnail` URL from `GetPublishedFileDetails`. The site lazy-loads the previews directly from Steam. The required ZombieBuddy setup links are in `mods.html`.
- The **Update public player roster** workflow checks the game's public Steam A2S endpoint about every five minutes and publishes `status.json` on the dedicated `server-status` branch. The site reads that file without contacting the admin panel or needing a token. A failed check is shown as unreachable; older snapshots expire in the UI after 20 minutes. Player names appear only when the Steam query returns them.
- GitHub may delay scheduled checks. To refresh on demand or re-enable a paused schedule, use **Actions → Update public player roster**.

## Site language

The header switcher remembers a visitor's choice in local storage. Without a saved choice, the site calls [Country.is](https://country.is/) once per session and uses the two-letter country code: Indonesia defaults to Indonesian, and other countries or failed lookups default to English. The lookup uses the visitor's public IP; the site stores only the country code for the session. Page translations and localized messages are in `language.js`.
