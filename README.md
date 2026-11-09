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
