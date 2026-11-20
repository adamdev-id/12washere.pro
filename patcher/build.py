"""Build the Windows binary and both requested offline player packages."""
import hashlib
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT.parent / 'downloads'
OUTPUT.mkdir(exist_ok=True)
subprocess.run([
    sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', '--onefile',
    '--windowed', '--name', '12washere.pro-Patcher',
    '--icon', str(ROOT / 'patcher.ico'), '--version-file', str(ROOT / 'version.txt'),
    '--add-data', str(ROOT / 'payload') + ';payload',
    '--add-data', str(ROOT / 'THIRD-PARTY-NOTICES.txt') + ';.',
    '--distpath', str(OUTPUT), '--workpath', str(ROOT / '.build'),
    '--specpath', str(ROOT), str(ROOT / 'app.py'),
], check=True)
readme = (ROOT / 'PLAYER-README.txt').read_bytes()
(OUTPUT / 'README.txt').write_bytes(readme)
(OUTPUT / 'THIRD-PARTY-NOTICES.txt').write_bytes((ROOT / 'THIRD-PARTY-NOTICES.txt').read_bytes())
with zipfile.ZipFile(OUTPUT / '12WASHERE-Updated-Client-Package.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
    archive.write(OUTPUT / '12washere.pro-Patcher.exe', '12washere.pro-Patcher.exe')
    archive.writestr('README.txt', readme)
    archive.write(ROOT / 'THIRD-PARTY-NOTICES.txt', 'THIRD-PARTY-NOTICES.txt')
with zipfile.ZipFile(OUTPUT / '12WashereSpawnMenuFix.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
    mod = ROOT / 'local-mod/12WashereSpawnMenuFix'
    for file in sorted(mod.rglob('*')):
        if file.is_file():
            archive.write(file, 'mods/12WashereSpawnMenuFix/' + file.relative_to(mod).as_posix())
    archive.writestr('README.txt', '12WashereSpawnMenuFix 1.1.0 - optional local mod, no Workshop upload.\n\nThe recommended multiplayer installation is 12washere.pro-Patcher.exe, which\napplies these assets directly and also fixes custom outfit preset loading.\nYou do not need to activate this local mod when using the patcher.\n\nFor local-mod use, copy mods/12WashereSpawnMenuFix into your Zomboid/mods\nfolder and enable it through the game Mods screen where appropriate.\nRequires Louisville_Quarantine_Zone. This archive contains spawn-menu\nmetadata and EN/ID clothing labels only; it has no preset-reader patch.\nIt does not change server settings or download any Workshop items.\n')
names = ['12washere.pro-Patcher.exe', '12WASHERE-Updated-Client-Package.zip', '12WashereSpawnMenuFix.zip']
checksums = '\n'.join(hashlib.sha256((OUTPUT / name).read_bytes()).hexdigest() + '  ' + name for name in names) + '\n'
(OUTPUT / 'SHA256SUMS.txt').write_text(checksums, encoding='ascii')
for name in names:
    if name.endswith('.zip'):
        with zipfile.ZipFile(OUTPUT / name) as archive:
            assert archive.testzip() is None
print(checksums)
