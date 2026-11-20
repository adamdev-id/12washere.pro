# 12washere.pro Patcher

Windows desktop patcher for the client-side spawn metadata, clothing labels and
outfit preset colon-parser fix. There is no server connection or Workshop upload.

## Build

On Windows x64, use Python 3.14 with Tkinter installed:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r patcher/requirements-build.txt
.venv\Scripts\python -m unittest discover -s patcher -v
.venv\Scripts\python patcher/build.py
```

The standalone executable and player ZIPs are written to `downloads/`. Players
do not need Python. PyInstaller is a build-time tool; psutil is bundled to detect
normal and alternate Java launches. This first release is unsigned.

## Maintenance

- `payload/manifest.json` hashes every bundled metadata file and patch input.
- `payload/preset-before.lua` and `preset-after.lua` are the exact supported
  reader before/after. The whole reader and file-format version must match.
- Review a new game build before refreshing those supported blocks. Never
  broaden the patch to blind text replacement.
- Clothing UI additions are merged only where a label is missing or raw.
- The preset fix changes checksummed client Lua. Servers enforcing Lua checks
  must match that file. No checksum bypass or server setting change is made.
- A game-directory whitelist and resolved-path checks constrain writes. Saves,
  Workshop content, `Mods=`, `WorkshopItems=` and Steam credentials are untouched.
- Preflight validates all components before modifying game files. Each patch
  keeps originals and a transaction record, performs atomic file replacement,
  and verifies afterward. A failed operation rolls back when the game is closed.
- If the game starts mid-patch, an interrupted transaction can be restored after
  closing it. Patch is refused until that recovery is completed.
- Restore preflights every file against before/after hashes. Changes made since
  patching cause an all-files preflight refusal, preserving later updates.
- A per-installation OS file lock prevents concurrent patch/restore operations.
- Running-game checks occur in the UI and again inside every write operation.
  Unreadable Java processes block writes rather than guessing.
- Backups are in `%LOCALAPPDATA%/12washere.pro/Patcher/backups/<game-id>/`.

Tests use temporary game fixtures, not a real game installation. Manual UI
verification covers English/Indonesian and blocked buttons with a real running
Project Zomboid process. The prior Lua regression harness exercised the actual
game reader, writer and `loadOutfit` with vanilla/custom slots, colors and textures.

The ZIP local-mod edition includes spawn metadata and clothing labels only.
The parser fix is installed directly by the patcher. It is not a full replacement
`CharacterCreationMain.lua` mod, which could overwrite other UI fixes.
