# 12WASHERE — Project Zomboid landing page

[12washere.pro](https://12washere.pro/) is a static site published by GitHub Pages from the root of `main`. The custom domain is set in `CNAME` and the repository's Pages settings. No build step is required.

## Joining

In Project Zomboid, open **Join** and enter `pz.12washere.pro` as the hostname and `7449` as the port. The site copies the values shown next to each Copy button. The Steam link opens the game, where players finish joining.

The game hostname points to the separate Google Cloud server. Keep its game DNS record unproxied so players can reach the UDP game port. The landing page does not query or control the game server.

## Editing

- `index.html`: page copy and connection details. Update each displayed instance if the hostname or port changes; the Copy buttons read directly from the adjacent `<code>` element.
- `script.js`: Join dialog and clipboard controls. Increment the `?v=` on its URL in `index.html` when changing it so returning visitors fetch the new script.
- `style.css` and `assets/`: layout, colors, and SVG artwork. Google Fonts has local system-font fallbacks.

Without JavaScript, the Join links go to the connection section, where players can copy the details manually.

## Player roster and modlist

- `mods.json` lists the configured Steam Workshop items, one card per Workshop ID. Update it from the server's `WorkshopItems=` list when that list changes. Each item has a primary `category` (see `categoryLabels` in `mods.js`) and a Steam Workshop `thumbnail` URL from `GetPublishedFileDetails`. The site lazy-loads the previews directly from Steam. The required ZombieBuddy setup links are in `mods.html`.
- The **Update public player roster** workflow checks the game's public Steam A2S endpoint about every five minutes and publishes `status.json` on the dedicated `server-status` branch. The site reads that file without contacting the admin panel or needing a token. A failed check is shown as unreachable; older snapshots expire in the UI after 20 minutes. Player names appear only when the Steam query returns them.
- GitHub may delay scheduled checks. To refresh on demand or re-enable a paused schedule, use **Actions → Update public player roster**.

## Site language

The header switcher remembers a visitor's choice in local storage. Without a saved choice, the site calls [Country.is](https://country.is/) once per session and uses the two-letter country code: Indonesia defaults to Indonesian, and other countries or failed lookups default to English. The lookup uses the visitor's public IP; the site stores only the country code for the session. Page translations and localized messages are in `language.js`.
