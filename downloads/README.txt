12washere.pro Patcher 1.6.0
Windows 10/11 x64 | Project Zomboid Build 42.22 preset format 1

QUICK START
1. Fully close Project Zomboid. Leave any Steam game update to finish first.
2. Extract the ZIP if applicable, then run 12washere.pro-Patcher.exe.
   Python, .NET and a Workshop upload are not needed.
3. The patcher detects Steam and its registered libraries. Select your Project
   Zomboid installation if more than one is found, or use Browse to find the
   folder containing ProjectZomboid64.exe.
4. Click Patch game. Wait until it reports patched and verified.
5. Launch Project Zomboid again. Load your outfit preset before saving over it.
6. With Autodrive, Viewpoint and ZombieBuddy installed, enable "Derpy Autodrive
   - Viewpoint Routes" under Viewpoint settings: Delete > Add-ons. Keep Panini
   projection off. The server must enable this local mod for multiplayer.
7. In the add-on's General Settings, choose a display independently for each
   camera: Navigation HUD, Road Guidance, Both, or Off. Defaults are Navigation
   HUD in first person and Road Guidance in third person.
8. Destination Guidance (yellow) and Trajectory Guidance (green) each have
   an Enabled switch (default ON). Hide either road overlay independently,
   keeping the HUD and the other route. Each also has its own Line/Arrow
   selector, line width, brightness, arrow size/spacing,
   animation speed, and pulse/fade. Defaults: yellow arrows and green line.
9. Navigation HUD defaults to 3D Direction Arrow with Car Heading; Turn Arrow
   is also available. Animation
   is ON by default, with adjustable speed/intensity. Turn Arrow flows a light
   through the turn shape; 3D Direction Arrow follows the road ahead using
   Car Heading (default) or Player POV. Car Heading ignores looking around. Its look-away fading defaults OFF. Turning animation
   off still lets the 3D arrow track camera direction. HUD position, size and
   brightness are independent. It works with either camera or road overlays off.
   Saved player styles stay selected; choose 3D Direction Arrow and Car Heading
   once to switch an existing profile to the new defaults.
   3D Turn anticipation (default 25 m) previews the planned green path through
   bends, even when hidden. Rotation smoothness (default 0.3 s) eases changes.
10. Match destination length to green trajectory stays on by default. It
    shortens either yellow lines or arrows at the green endpoint. Autodrive's
    own Navigation line and Trajectory toggles still control their road overlay.


The warning "Project Zomboid is running. Please close it before patching or
restoring" disables Patch and Restore. The patcher never closes your game.
Verify and Steam detection are read-only and can be used while the game is open.

WHAT IS INCLUDED
- 12WashereSpawnMenuFix descriptions and previews for the seven extra ,KY
  spawn regions plus Louisville Quarantine Zone. Spawn positions stay unchanged.
- 31 missing ALICE, J&G and KATTAJ1 clothing-slot labels in English/Indonesian.
  Existing UI translations are preserved.
- A preset reader fix: only the FIRST colon separates a preset name from its
  data. Custom slots such as KATTAJ1:BackFanny retain their names and item data,
  including color and texture selections.
- Derpy Autodrive - Viewpoint Routes 0.5.3: independent yellow/green
  Line or Arrow guidance, with per-camera road/HUD display selectors.
  Installed to %USERPROFILE%\Zomboid\mods\DerpyAutodriveViewpoint. Requires
  Autodrive, Viewpoint 0.1.7 / API 1.0.0 and ZombieBuddy, installed separately.

Spawn, label and preset fixes are installed directly into the client's game
files. The route add-on is installed as a local mod; it has no Workshop ID.
For multiplayer, the server must have the same route mod and include
DerpyAutodriveViewpoint in Mods=. The patcher does not edit server settings.
The optional 12WashereSpawnMenuFix.zip is the local-mod edition of the spawn
and label assets. You do not need to enable that local mod when using this
patcher. The preset parser fix is provided by the patcher, not by that mod ZIP.
DerpyAutodriveViewpoint.zip provides the route add-on for manual installation.
The patcher EXE already contains it, so Windows patcher users do not need that ZIP.

BACKUPS AND RESTORE
- Before changing anything, the patcher validates every planned change and
  backs up each existing file it will replace.
- Backups/logs are stored at %LOCALAPPDATA%\12washere.pro\Patcher.
- Restore backup undoes the latest active patch for the selected installation.
  Newly added game and route-mod files are removed; existing files are restored.
- Restore refuses files changed since patching, protecting later Steam updates
  or edits. It does not overwrite them to force an old backup into place.
- An interrupted patch keeps a recovery record. Close the game, then Restore
  backup before trying Patch game again. Keep backups until recovery completes.
- An already patched installation is verified without creating a new backup.
  Files patched earlier by another method cannot be restored by this tool.

LIMITS
- Windows only. Use the same game build as the server. An unfamiliar preset
  reader is refused without applying the other changes.
- Already truncated and overwritten outfit selections cannot be reconstructed.
  Reselect missing items and save again after patching. Intact presets can load.
- Character, world and vehicle saves are never edited. This patcher does not
  repair corrupt characters, server world maps, mod conflicts or missing mods.
- Autodrive, Viewpoint, other Workshop mods and ZombieBuddy remain separate installations. See
  https://12washere.pro/mods.html for server requirements.
- Steam updates or Verify Files can replace these fixes. Run Verify in this
  patcher afterward, and Patch game again if it recognizes the new game code.
- The outfit preset fix changes a client Lua file. Servers enforcing Lua
  checksums need a matching server-side file, otherwise they can reject joining.
  This patcher never changes checksum settings or patches a remote server.
  Restore before joining a server that requires the unmodified client file.
- The executable is unsigned. Windows may identify the publisher as unknown.
  Compare the SHA-256 with SHA256SUMS.txt from the same trusted download source.
- If Windows refuses write access, close game/Steam updates. Administrator
  rights may be required for games installed in protected directories.
- The patcher works offline. It never uploads files, reads Steam credentials,
  subscribes to mods, or changes the dedicated server.
- The new guidance passed geometry, game Lua, loader and GPU checks. Its
  animated display still needs an actual driving-session check. It targets player one's normal Viewpoint
  camera; Panini, Minecraft/Iris packs and split-screen are not supported.

SUPPORT
https://12washere.pro/
https://discord.gg/3qPv6cNpSZ

SOURCE / CREDITS
The patcher source is in the 12washere.pro repository under patcher/.
Project Zomboid is by The Indie Stone. Louisville preview assets originate
from Louisville Quarantine Zone (Workshop 2934132344). Original localized town
metadata is from the installed game. Credits/ownership of those assets remain
with their authors. This is an independent compatibility tool.
Python, Tcl/Tk, psutil and PyInstaller have their own licenses. See
patcher/THIRD-PARTY-NOTICES.txt in the source repository.

APPROVED SERVER MODS
Use Check release, then Sync approved mods with Project Zomboid closed.
Only the published release from https://pz.12washere.pro is downloaded.
Draft updates in PZ Panel are never distributed to players. Each file is
verified using its size and SHA-256 hash. Unchanged files are reused.
Mod snapshots are installed under Zomboid/mods/zcp_<WorkshopID>_<folder>.
Steam subscriptions and unrelated mods/saves are untouched. If you have
duplicate Workshop copies of the same Mod ID, keep the approved local copy
active for this server. Separate Java/game loaders still need installation.
Restore mod release rolls back one release (and can recover interrupted
updates). Do not join a server using a different release after rollback.
Backups: Zomboid/.12washere-release-backups; records/cache: LocalAppData/
12washere.pro/Patcher/approved-mods. Never delete backups during recovery.
No approved release yet is normal until the administrator publishes one.
Game fixes / Restore backup are independent from approved server mods.

Use Play approved release in the patcher after syncing. It starts Steam with
-modfolders mods,steam,workshop, putting approved local mods ahead of Steam
copies with the same Mod ID. For direct Steam launches, set that same text
in Project Zomboid > Properties > Launch Options. Without this option, PZ
can choose an updated Workshop copy instead of the approved local copy.
