# 12washere.pro Patcher

Windows desktop patcher for the client-side spawn metadata, clothing labels and
outfit preset colon-parser fix. Version 1.5.3 also installs the bundled Derpy
Autodrive Viewpoint route add-on to `%USERPROFILE%/Zomboid/mods/DerpyAutodriveViewpoint`.
Version 1.6.0 adds approved server releases from PZ Panel at
`https://pz.12washere.pro/api/mod-releases/9059cf4f988a72fe963e87c8/latest`.
The existing game fixes work offline; **Sync/Patch Mods from Server** fetches only the
published release, verifies hashes, and manages separate `zcp_*` local folders.
Draft downloads are never distributed. **Play approved release** verifies the
release and launches Steam with `-modfolders mods,steam,workshop`. Direct Steam
launches need that option too, to prefer local copies over Workshop copies.
Unmanaged local folders providing duplicate Mod IDs are refused. There is no
Workshop upload. See `C:\Github\zomboid-control-panel\docs\local-mod-releases.md`
for the panel protocol, deployment, and publication/recovery workflow.

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
- The six files under `payload/local-mods/DerpyAutodriveViewpoint/` are part of
  the same verified, reversible transaction as the game fixes. Exact mod paths
  are whitelisted separately from game paths; unrelated mods are untouched.
- The add-on requires Autodrive, Viewpoint 0.1.7 / API 1.0.0 and ZombieBuddy.
  Players enable it in Viewpoint's Add-ons section after installation. Their
  server must include `DerpyAutodriveViewpoint` in `Mods=` and have the same files.
  No Workshop entry is needed for the local add-on.
- `payload/preset-before.lua` and `preset-after.lua` are the exact supported
  reader before/after. The whole reader and file-format version must match.
- Review a new game build before refreshing those supported blocks. Never
  broaden the patch to blind text replacement.
- Clothing UI additions are merged only where a label is missing or raw.
- The preset fix changes checksummed client Lua. Servers enforcing Lua checks
  must match that file. No checksum bypass or server setting change is made.
- A game-file and local-mod whitelist with resolved-path checks constrains writes. Saves,
  Workshop content, `Mods=`, `WorkshopItems=` and Steam credentials are untouched.
- Preflight validates all components before modifying game files. Each patch
  keeps originals and a transaction record, performs atomic file replacement,
  and verifies afterward. A failed operation rolls back when the game is closed.
- If the game starts mid-patch, an interrupted transaction can be restored after
  closing it. Patch is refused until that recovery is completed.
- Restore preflights every file against before/after hashes. Changes made since
  patching cause an all-files preflight refusal, preserving later updates.
- A per-installation OS file lock prevents concurrent patch/restore operations.
- A second lock covers the shared player mods directory across game installations.
- New transactions record the player mods directory; Restore refuses a different
  player directory. Version 1.0.0 game-only backups remain restorable.
- Running-game checks occur in the UI and again inside every write operation.
  Unreadable Java processes block writes rather than guessing.
- Backups are in `%LOCALAPPDATA%/12washere.pro/Patcher/backups/<game-id>/`.

Tests use temporary game fixtures, not a real game installation. Manual UI
verification covers English/Indonesian and blocked buttons with a real running
Project Zomboid process. The prior Lua regression harness exercised the actual
game reader, writer and `loadOutfit` with vanilla/custom slots, colors and textures.

The `12WashereSpawnMenuFix.zip` local-mod edition includes spawn metadata and clothing labels only.
The parser fix is installed directly by the patcher. It is not a full replacement
`CharacterCreationMain.lua` mod, which could overwrite other UI fixes.
`DerpyAutodriveViewpoint.zip` is the separate manual route add-on package for
players who need it without the Windows patcher. The EXE already includes it.

The route add-on's Lua/API/GPU checks passed during development. Its first-
and third-person alignment still needs verification in an actual driving
session, including multiplayer. Panini and Minecraft/Iris shader pipelines are
outside this first build's support. Existing camera controls are unchanged.

The route 0.1.2 regression compares its actual render batches against the installed Viewpoint world-to-screen implementation on 32 endpoints, including a real relief grid and fractional camera elevations. This caught and corrects the horizontal-axis mismatch in earlier builds.

Route add-on 0.2.0 includes a persisted live Viewpoint toggle, default on, that clips the yellow route at the green trajectory endpoint. Tests exercise live changes, segment interpolation, bends, lane offsets, overlapping loops, and the no-trajectory preview. The settings schema is validated with the installed Viewpoint parser.

Route add-on 0.5.0 provides independent Destination (yellow) and Trajectory
(green) Line/Arrow styles. Each has its own width, brightness, arrow size,
spacing, animation speed and pulse/fade. General Settings select Navigation
HUD, Road Guidance, Both, or Off separately per camera; defaults are HUD in
first person and Road Guidance in third person. HUD appearance is independent.
All 31 controls apply live. Native/game-Lua checks cover all camera options,
all four line/arrow pairings, isolated appearance changes, route visibility,
HUD with road toggles off, and preserved green-horizon clipping.

Add-on 0.4.1 fixes the render-thread access to Viewpoint's main-thread-only
camera API introduced in 0.4.0. Road visibility now travels in the main-thread
guidance snapshot. Regression callbacks run on another thread with camera
and settings access guarded, matching the host's thread restrictions.

Add-on 0.4.2 adds an Enabled toggle (default ON) at the top of both Destination
and Trajectory settings. Each applies live to that route's lines or arrows;
all four enabled/disabled combinations are tested for every Line/Arrow pairing.
The Navigation HUD and the other route retain their settings and visibility.

Add-on 0.5.0 adds an animated Turn Arrow (default) and a shaded, extruded 3D
Direction Arrow to the Navigation HUD. The main thread derives camera-relative
yaw/pitch from a target ahead along the route, including terrain elevation.
UI polygons render the 3D mesh through the game's existing UI renderer.
Animation can be disabled or tuned by speed and intensity; 3D look-away fade
has its own default-OFF control. Road style and enabled settings are retained.
Checks cover direction, pitch, angle wrap, live animation controls, stable text,
mesh bounds at three resolutions, and main/render thread separation. Actual
Lua draw commands are exported for static/animated visual inspection.


Version 0.5.1 previews the green planned trajectory through upcoming bends,
even when that overlay is hidden. When no useful trajectory exists, it uses
the destination route. The target no longer stops at the next corner.
3D arrow controls: Turn anticipation defaults to 25 m (5-60 m); Rotation
smoothness defaults to 0.3 s (0.05-1 s). More anticipation looks farther ahead;
more smoothness makes direction changes gentler. Both apply live. The 3D
Direction Arrow with Car Heading is the default, and 3D look-away fading stays off by default.


Version 0.5.2 adds 3D arrow: direction reference, with Car Heading as the default.
Car Heading uses the car's forward direction and position, so head/camera yaw,
pitch and position do not change arrow orientation. Planned-trajectory turn
anticipation, road-grade tilt and rotation smoothing continue to apply.
Player POV retains camera-relative orientation. The choice applies live under
Navigation HUD and only affects the 3D Direction Arrow. The overall default
is the 3D Direction Arrow with Car Heading; 3D look-away fading remains off by default.


Version 0.5.3 makes 3D Direction Arrow with Car Heading the default HUD style.
Arrow animation remains enabled and 3D look-away fading stays off. Turn Arrow
and Player POV remain available. New defaults apply to fresh/default settings;
previously saved player choices are preserved. Existing players can select
3D Direction Arrow and Car Heading once under Navigation HUD to switch.

## Server mod browser (1.7.0)

`mods_view.py` renders Needs Update / Latest with shared column definitions
and a single whole-release Sync/Patch action in Needs Update. `releases.py`
`inspect()` compares actual local file hashes with the approved manifest;
stored version labels alone never mark a mod current. It groups files by
Workshop item, accepts optional per-mod update dates and derives revisions
for legacy manifests. The existing public thumbnail proxy provides cached
44px mod images; Pillow is bundled in the EXE. Failed images use a placeholder.

Checks run off the Tk thread. A failed refresh keeps old rows visibly stale
and disables Sync/Play until a successful refresh. Owned changed folders are
backed up before repair, with actual pre-sync hashes journaled for recovery.
Unmanaged folders are still never overwritten. Restore remains separate.
Tests: `test_mods_view.py`, `test_releases.py`, and the existing core suite.
