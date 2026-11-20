12washere.pro Patcher 1.0.0
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

No Mods= or WorkshopItems= changes are needed. Fixes are installed directly
into the client's game files. This patcher does not install a Workshop mod.
The optional 12WashereSpawnMenuFix.zip is the local-mod edition of the spawn
and label assets. You do not need to enable that local mod when using this
patcher. The preset parser fix is provided by the patcher, not by that mod ZIP.

BACKUPS AND RESTORE
- Before changing anything, the patcher validates every planned change and
  backs up each existing file it will replace.
- Backups/logs are stored at %LOCALAPPDATA%\12washere.pro\Patcher.
- Restore backup undoes the latest active patch for the selected installation.
  Newly added files from that patch are removed; existing files are restored.
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
- Workshop mods and ZombieBuddy remain separate installations. See
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
