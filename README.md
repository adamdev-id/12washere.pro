# 12WASHERE — Project Zomboid landing page

A responsive, static site for **12washere.pro**. No build tools or installation needed. Includes an original SVG illustration, accessible Join dialog, copy controls, Steam game launcher, mobile layout, reduced-motion support, favicon, and custom-domain file.

## Publish on GitHub Pages

1. Sign in as **adamdev-id**, then create a public repository named **12washere-site** (or use an existing website repository).
2. Upload the **contents** of this folder to its root: `index.html`, `style.css`, `script.js`, `assets/`, `CNAME`, and `.nojekyll`. Keep `assets/` as a folder. Do not upload the ZIP itself or nest everything inside another folder.
3. In **Settings → Pages**, choose **Deploy from a branch → main → / (root) → Save**.
4. Set **Custom domain** to `12washere.pro` and save **before** changing DNS. The included CNAME file contains that domain.
5. Apply the Cloudflare records below. When GitHub's certificate is available, enable **Enforce HTTPS**.

Your default Pages URL would be `https://adamdev-id.github.io/12washere-site/`; after the custom domain is configured, the public URL is `https://12washere.pro/`.

## Cloudflare → DNS → Records

Use **DNS only** (gray cloud) for these records during setup. TTL: Auto.

| Type | Name | Content | Proxy |
| --- | --- | --- | --- |
| A | @ | 185.199.108.153 | DNS only |
| A | @ | 185.199.109.153 | DNS only |
| A | @ | 185.199.110.153 | DNS only |
| A | @ | 185.199.111.153 | DNS only |
| CNAME | www | adamdev-id.github.io | DNS only |
| A | pz | 147.185.221.215 | **DNS only — keep this unproxied** |

Replace conflicting web A/AAAA/CNAME records at `@` and `www`. Preserve unrelated email MX/TXT records. The four root A records coexist. The `www` record points to the GitHub **hostname**, without a repository path.

The `pz` record uses the IP you supplied. A lookup during preparation returned `91.243.81.136`, so verify which IP your server/tunnel provider currently assigns before replacing that record. A DNS record holds an IP **without a port**. Players connect to `pz.12washere.pro` with port `65008` in the game; `pz.12washerepro.65008` is not the correct connection address.

Cloudflare's standard web proxy does not carry this game traffic on port 65008. Keep `pz` DNS-only. Hosting the website at the root domain and the game on `pz` lets both work independently. This configuration serves the page **at your own domain**, instead of sending visitors away to a github.io address.

## Joining

The Join button opens instructions with separate hostname and port copy buttons. “Launch Project Zomboid” opens `steam://rungameid/108600`, which launches the installed game through Steam. It does **not** automatically enter the server; players finish in the game's Join menu. This avoids relying on an unverified server-connect URI. Steam must be installed on the player's PC.

The page is not a live server monitor and makes no claims about uptime, player count, rules, mods, password requirements, or supported game version. The supplied direct IP is offered as an alternative if hostname resolution fails; actual game connectivity must be tested from Project Zomboid.

## Editing

- Wording and displayed connection details: `index.html`.
- Copied connection values: the `server` object at the top of `script.js`. **Update both HTML and JavaScript** if the address or port changes.
- Colors, layout, breakpoints: `style.css`.
- Illustration and icon: `assets/` (original SVG artwork).
- Domain: `CNAME` plus GitHub Pages settings and DNS.

Google Fonts supplies Barlow Condensed, DM Sans, and Space Mono. System font fallbacks keep the page usable if fonts are blocked. Everything else is included locally. JavaScript is optional for viewing the page; without it, Join links go to the connection section.

## Sources

- [GitHub: publishing from a branch](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
- [GitHub: custom domain and published DNS addresses](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site)
- [Cloudflare: supported proxy ports](https://developers.cloudflare.com/fundamentals/reference/network-ports/)

Files are ready for upload. GitHub publishing and Cloudflare changes require account access and have not been performed as part of creating this package.
