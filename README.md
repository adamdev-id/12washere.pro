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
- `donation.html`, `donation.css`, and `donation.js`: donation page with recent donations first, separate Saweria and QRIS actions, the donation goal, and the leaderboard. The QRIS action opens a fading native dialog; without JavaScript it links directly to the supplied widget. The QR encodes the same donation URL as Saweria's QR widget: visitors open Saweria and select QRIS there. Donation page translations are in `language.js`.
- Saweria's widget pages send `X-Frame-Options: SAMEORIGIN`, and its data API blocks browser CORS requests. The **Update public donation data** workflow reads the public widget API about every five minutes and publishes `donation-status.json` on the separate `donation-status` branch. The page uses the newest of that data and the initial checked-in snapshot, shows its timestamp, and marks data older than 20 minutes as delayed. The widget links remain available for the current Saweria view. Run `python scripts/query-donations.py donation-status.json` to refresh the local snapshot. No Saweria account credentials are required; the supplied public widget key is used only to read widget data.

Without JavaScript, the Join links go to the connection section, where players can copy the details manually.

## Player roster and modlist

- `mods.json` lists the configured Steam Workshop items, one card per Workshop ID. Update it from the server's `WorkshopItems=` list when that list changes. Each item has a primary `category` (see `categoryLabels` in `mods.js`) and a Steam Workshop `thumbnail` URL from `GetPublishedFileDetails`. The site lazy-loads the previews directly from Steam. The required ZombieBuddy setup links are in `mods.html`.
- The **Update public player roster** workflow checks the game's public Steam A2S endpoint about every five minutes and publishes `status.json` on the dedicated `server-status` branch. The site reads that file without contacting the admin panel or needing a token. A failed check is shown as unreachable; older snapshots expire in the UI after 20 minutes. Player names appear only when the Steam query returns them.
- GitHub may delay scheduled checks. To refresh on demand or re-enable a paused schedule, use **Actions → Update public player roster**.

## Site language

The header switcher remembers a visitor's choice in local storage. Without a saved choice, the site calls [Country.is](https://country.is/) once per session and uses the two-letter country code: Indonesia defaults to Indonesian, and other countries or failed lookups default to English. The lookup uses the visitor's public IP; the site stores only the country code for the session. Page translations and localized messages are in `language.js`.
