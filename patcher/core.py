"""Local-only, reversible client patching. No server or personal saves are edited."""
from __future__ import annotations

from dataclasses import dataclass
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import uuid

VERSION = '1.5.3'
PRESET_PATH = 'media/lua/client/OptionScreens/CharacterCreationMain.lua'
UI_PATHS = {f'media/lua/shared/Translate/{lang}/UI.json' for lang in ('EN', 'ID')}
GAME_NAMES = {'projectzomboid.exe', 'projectzomboid64.exe', 'projectzomboid32.exe'}
MOD_PREFIX = 'local-mods/DerpyAutodriveViewpoint/'
MOD_PATHS = {MOD_PREFIX + path for path in (
    'README.md', 'common/mod.info', '42/media/lua/client/DerpyAutodriveViewpoint.lua',
    'common/media/viewpoint/addons/derpy.autodrive-viewpoint/addon.properties',
    'common/media/viewpoint/addons/derpy.autodrive-viewpoint/DerpyAutodriveViewpoint.jar',
    'common/media/viewpoint/addons/derpy.autodrive-viewpoint/settings.properties',
)}


class PatchError(Exception):
    def __init__(self, code, detail=''):
        self.code, self.detail = code, detail
        super().__init__(detail or code)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def state_dir():
    return Path(os.environ.get('LOCALAPPDATA', str(Path.home() / 'AppData/Local'))) / '12washere.pro/Patcher'


def payload_dir():
    return Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent)) / 'payload'


def parse_vdf(text):
    """Parse quoted Valve KeyValues, including escaped Windows paths and comments."""
    raw = re.findall(r'//[^\n]*|"(?:\\.|[^"\\])*"|[{}]', text)
    tokens = [token for token in raw if not token.startswith('//')]
    cursor = 0

    def value(token):
        if not token.startswith('"'):
            raise ValueError('Expected quoted Valve value')
        return re.sub(r'\\(["\\])', r'\1', token[1:-1])

    def object_(nested=False):
        nonlocal cursor
        result = {}
        while cursor < len(tokens):
            token = tokens[cursor]
            cursor += 1
            if token == '}':
                if not nested:
                    raise ValueError('Unexpected closing brace')
                return result
            key = value(token)
            if cursor == len(tokens):
                raise ValueError('Missing Valve value')
            token = tokens[cursor]
            cursor += 1
            result[key] = object_(True) if token == '{' else value(token)
        if nested:
            raise ValueError('Unclosed Valve object')
        return result

    return object_()


def steam_roots():
    if os.name != 'nt':
        return []
    import winreg
    paths = []
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        for view in (winreg.KEY_WOW64_32KEY, winreg.KEY_WOW64_64KEY):
            try:
                with winreg.OpenKey(hive, r'Software\Valve\Steam', 0, winreg.KEY_READ | view) as key:
                    for name in ('SteamPath', 'InstallPath', 'SteamExe'):
                        try:
                            path = Path(winreg.QueryValueEx(key, name)[0])
                            paths.append(path.parent if name == 'SteamExe' else path)
                        except OSError:
                            pass
            except OSError:
                pass
    for name in ('ProgramFiles(x86)', 'ProgramFiles'):
        if os.environ.get(name):
            paths.append(Path(os.environ[name]) / 'Steam')
    return list(dict.fromkeys(path.resolve() for path in paths))


def detect_games(roots=None):
    libraries = list(steam_roots() if roots is None else map(Path, roots))
    for steam in list(libraries):
        try:
            data = parse_vdf((steam / 'steamapps/libraryfolders.vdf').read_text(encoding='utf-8-sig'))
            for key, item in data.get('libraryfolders', {}).items():
                path = item.get('path') if isinstance(item, dict) else item if key.isdigit() else None
                if path:
                    libraries.append(Path(path))
        except (OSError, ValueError, AttributeError):
            pass
    found = []
    for library in dict.fromkeys(path.resolve() for path in libraries):
        try:
            manifest = parse_vdf((library / 'steamapps/appmanifest_108600.acf').read_text(encoding='utf-8-sig'))['AppState']
            if manifest.get('appid') != '108600':
                continue
            common = (library / 'steamapps/common').resolve()
            game = (common / manifest['installdir']).resolve()
            if game == common or not game.is_relative_to(common):
                continue
            validate_game(game)
            found.append(game)
        except (OSError, ValueError, KeyError, TypeError, PatchError):
            pass
    return list(dict.fromkeys(found))


def validate_game(game):
    game = Path(game).resolve()
    required = ['projectzomboid.jar', PRESET_PATH, 'media/lua/shared/Translate/EN/Muldraugh, KY.json', *UI_PATHS]
    if not all((game / relative).is_file() for relative in required) or not any((game / name).is_file() for name in ('ProjectZomboid64.exe', 'ProjectZomboid32.exe', 'ProjectZomboid.exe')):
        raise PatchError('wrong_folder', 'Select the Windows Project Zomboid game folder, not Steam, Workshop, or the Dedicated Server folder.')
    return game


def running_game_processes():
    """Recognize native and alternate Java launches; fail closed on unreadable Java."""
    import psutil
    found = []
    try:
        for process in psutil.process_iter(['pid', 'name']):
            name = (process.info.get('name') or '').lower()
            if name in GAME_NAMES:
                found.append(f'{name} (PID {process.pid})')
            elif name in ('java.exe', 'javaw.exe'):
                try:
                    command = ' '.join(process.cmdline()).lower().replace('\\', '/')
                    executable = process.exe().lower().replace('\\', '/')
                except psutil.NoSuchProcess:
                    continue
                except psutil.AccessDenied:
                    raise PatchError('process_unknown', f'Cannot inspect Java process {process.pid}. Close it or run the patcher with matching permissions.')
                if any(marker in command for marker in ('zombie.gamewindow', 'zombie.gamestates.main', 'zombie.network.gameserver', 'projectzomboid.jar')) or '/projectzomboid/' in executable:
                    found.append(f'{name} (PID {process.pid})')
    except psutil.Error as exc:
        raise PatchError('process_unknown', str(exc)) from exc
    return found


def ensure_closed():
    processes = running_game_processes()
    if processes:
        raise PatchError('game_running', '\n'.join(processes))


@dataclass
class Change:
    relative: str
    before: bytes | None
    after: bytes


class Engine:
    def __init__(self, payload=None, storage=None, guard=None, mods=None):
        self.payload = Path(payload or payload_dir()).resolve()
        self.storage = Path(storage or state_dir()).resolve()
        self.guard = guard or ensure_closed
        self.mods = Path(mods if mods is not None else Path.home() / 'Zomboid/mods').resolve()
        self.manifest = json.loads((self.payload / 'manifest.json').read_text(encoding='utf-8'))
        self.files = self.manifest['files']
        self.allowed = set(self.files) | UI_PATHS | {PRESET_PATH}
        for relative in self.allowed:
            if '\\' in relative or Path(relative).is_absolute() or '..' in Path(relative).parts or not (relative.startswith('media/') or relative in MOD_PATHS):
                raise PatchError('payload_invalid', relative)
        if not MOD_PATHS.issubset(self.files):
            raise PatchError('payload_invalid', 'The Viewpoint route add-on is incomplete.')
        for relative, expected in self.files.items():
            path = self.payload / relative
            try:
                valid = path.resolve().is_relative_to(self.payload) and sha(path.read_bytes()) == expected
            except OSError:
                valid = False
            if not valid:
                raise PatchError('payload_invalid', relative)
        self.labels = json.loads((self.payload / 'clothing-labels.json').read_text(encoding='utf-8'))
        if set(self.labels) != {'EN', 'ID'}:
            raise PatchError('payload_invalid', 'Unexpected translation languages')
        for lang, labels in self.labels.items():
            if len(labels) != 31 or not all(k.startswith(('UI_ClothingType_ALICE:', 'UI_ClothingType_KATTAJ1:', 'UI_ClothingType_Jordanals:')) and isinstance(v, str) and v.strip() for k, v in labels.items()):
                raise PatchError('payload_invalid', lang)
        self.preset_before = (self.payload / 'preset-before.lua').read_text(encoding='utf-8')
        self.preset_after = (self.payload / 'preset-after.lua').read_text(encoding='utf-8')
        for name in ('clothing-labels.json', 'preset-before.lua', 'preset-after.lua'):
            if sha((self.payload / name).read_bytes()) != self.manifest['support_files'][name]:
                raise PatchError('payload_invalid', name)

    def target(self, game, relative):
        if relative not in self.allowed:
            raise PatchError('unsafe_path', relative)
        root = self.mods if relative in MOD_PATHS else game
        destination = relative.removeprefix('local-mods/') if relative in MOD_PATHS else relative
        target = root / destination
        if not target.resolve().is_relative_to(root):
            raise PatchError('unsafe_path', relative)
        return target

    def plan(self, game):
        game = validate_game(game)
        changes = []
        counts = {'spawn': 0, 'labels': 0, 'presets': 0, 'viewpoint': 0}
        for relative in self.files:
            destination = self.target(game, relative)
            before = destination.read_bytes() if destination.exists() else None
            after = (self.payload / relative).read_bytes()
            if before != after:
                changes.append(Change(relative, before, after))
                counts['viewpoint' if relative in MOD_PATHS else 'spawn'] += 1
        for lang, labels in self.labels.items():
            relative = f'media/lua/shared/Translate/{lang}/UI.json'
            before = self.target(game, relative).read_bytes()
            try:
                current = json.loads(before.decode('utf-8-sig'))
                if not isinstance(current, dict) or not current:
                    raise ValueError('UI translations are not an object')
            except (ValueError, UnicodeError) as exc:
                raise PatchError('invalid_translation', relative) from exc
            additions = {key: value for key, value in labels.items() if not current.get(key) or current[key] == key}
            if additions:
                current.update(additions)
                changes.append(Change(relative, before, (json.dumps(current, ensure_ascii=False, indent=4) + '\n').encode('utf-8')))
                counts['labels'] += len(additions)
        before = self.target(game, PRESET_PATH).read_bytes()
        try:
            normalized = before.decode('utf-8-sig').replace('\r\n', '\n')
        except UnicodeError as exc:
            raise PatchError('unknown_parser') from exc
        if '\nlocal OUTFITS_VERSION = 1\n' not in normalized:
            raise PatchError('unknown_parser', 'The outfit file format has changed.')
        if normalized.count(self.preset_before) == 1 and self.preset_after not in normalized:
            newline = '\r\n' if b'\r\n' in before else '\n'
            patched = normalized.replace(self.preset_before, self.preset_after, 1).replace('\n', newline)
            if before.startswith(b'\xef\xbb\xbf'):
                patched = '\ufeff' + patched
            changes.append(Change(PRESET_PATH, before, patched.encode('utf-8')))
            counts['presets'] = 1
        elif normalized.count(self.preset_after) != 1 or self.preset_before in normalized:
            raise PatchError('unknown_parser', 'Unrecognized preset reader; the patcher has not changed any files.')
        return changes, counts

    def backup_root(self, game):
        key = sha(str(Path(game).resolve()).casefold().encode('utf-8'))[:16]
        return self.storage / 'backups' / key

    def backups(self, game):
        found = []
        for file in self.backup_root(game).glob('*/transaction.json'):
            try:
                data = json.loads(file.read_text(encoding='utf-8'))
                if os.path.normcase(data.get('game', '')) == os.path.normcase(str(Path(game).resolve())) and data.get('status') in ('installed', 'applying', 'needs_recovery', 'restoring'):
                    found.append((file, data))
            except (OSError, ValueError):
                continue
        return sorted(found, key=lambda item: item[0].parent.name, reverse=True)

    @staticmethod
    def write_atomic(path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + '.12washere-' + uuid.uuid4().hex + '.tmp')
        try:
            with temporary.open('xb') as output:
                output.write(data)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)

    def journal(self, path, data):
        self.write_atomic(path, (json.dumps(data, indent=2) + '\n').encode('utf-8'))

    @contextmanager
    def lock(self, game):
        # All installations share the same player mods directory. Lock that scope
        # as well as the selected game so two patchers cannot race on the add-on.
        mod_key = sha(str(self.mods).casefold().encode('utf-8'))[:16]
        with self._lock_file(self.storage / 'locks' / ('mods-' + mod_key)):
            with self._lock_file(self.backup_root(game)):
                yield

    @contextmanager
    def _lock_file(self, directory):
        directory.mkdir(parents=True, exist_ok=True)
        with (directory / 'operation.lock').open('a+b') as handle:
            handle.seek(0)
            try:
                if os.name == 'nt':
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise PatchError('another_patcher', 'Another patcher operation is using this installation.') from exc
            try:
                yield
            finally:
                handle.seek(0)
                if os.name == 'nt':
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def apply(self, game, progress=lambda *args: None):
        with self.lock(game):
            return self._apply(game, progress)

    def _apply(self, game, progress=lambda *args: None):
        self.guard()
        game = validate_game(game)
        changes, counts = self.plan(game)
        if any(data['status'] != 'installed' for _, data in self.backups(game)):
            raise PatchError('recovery_required')
        if not changes:
            return {'status': 'already_patched', 'counts': counts, 'changed_files': 0}
        self.guard()
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-' + uuid.uuid4().hex[:8]
        backup = self.backup_root(game) / stamp
        backup.mkdir(parents=True, exist_ok=False)
        entries = []
        for change in changes:
            if change.before is not None:
                self.write_atomic(backup / 'original' / change.relative, change.before)
            entries.append({'path': change.relative, 'before': sha(change.before) if change.before is not None else None, 'after': sha(change.after)})
        data = {'version': VERSION, 'game': str(game), 'mods': str(self.mods), 'status': 'applying', 'entries': entries}
        journal = backup / 'transaction.json'
        self.journal(journal, data)
        try:
            for index, change in enumerate(changes, 1):
                self.guard()
                target = self.target(game, change.relative)
                current = target.read_bytes() if target.exists() else None
                if current != change.before:
                    raise PatchError('files_changed', change.relative)
                self.write_atomic(target, change.after)
                progress(index, len(changes), change.relative)
            remaining, _ = self.plan(game)
            if remaining:
                raise PatchError('verification_failed')
        except Exception as exc:
            # Journal makes interrupted or partially applied work restorable on next run.
            data['status'] = 'needs_recovery'
            self.journal(journal, data)
            try:
                self.guard()
                self._restore(game, journal, data)
            except Exception:
                raise PatchError('recovery_required', f'Close the game and use Restore. Backup: {backup}. Cause: {exc}') from exc
            raise PatchError('rolled_back', str(exc)) from exc
        data['status'] = 'installed'
        self.journal(journal, data)
        return {'status': 'installed', 'counts': counts, 'changed_files': len(changes), 'backup': str(backup)}

    def _restore(self, game, journal, data, progress=lambda *args: None):
        operations = []
        entries = data.get('entries')
        if not isinstance(entries, list) or len({entry['path'] for entry in entries}) != len(entries):
            raise PatchError('backup_invalid')
        if any(entry['path'] in MOD_PATHS for entry in entries):
            if os.path.normcase(data.get('mods', '')) != os.path.normcase(str(self.mods)):
                raise PatchError('backup_invalid', 'This backup belongs to a different player mods folder.')
        for entry in entries:
            target = self.target(game, entry['path'])
            current = target.read_bytes() if target.exists() else None
            digest = sha(current) if current is not None else None
            if digest not in (entry['before'], entry['after']):
                raise PatchError('restore_conflict', entry['path'])
            original = None
            if entry['before'] is not None:
                saved = journal.parent / 'original' / entry['path']
                if not saved.resolve().is_relative_to(journal.parent.resolve()):
                    raise PatchError('unsafe_path', entry['path'])
                original = saved.read_bytes()
                if sha(original) != entry['before']:
                    raise PatchError('backup_invalid', entry['path'])
            if digest != entry['before']:
                operations.append((target, current, original, entry['path']))
        self.guard()
        data['status'] = 'restoring'
        self.journal(journal, data)
        for index, (target, expected, original, relative) in enumerate(operations, 1):
            self.guard()
            current = target.read_bytes() if target.exists() else None
            if current != expected:
                raise PatchError('restore_conflict', str(target))
            if original is None:
                target.unlink()
            else:
                self.write_atomic(target, original)
            progress(index, len(operations), relative)
        data['status'] = 'restored'
        self.journal(journal, data)
        return {'status': 'restored', 'restored_files': len(operations), 'backup': str(journal.parent)}

    def restore(self, game, progress=lambda *args: None):
        with self.lock(game):
            self.guard()
            game = validate_game(game)
            backups = self.backups(game)
            if not backups:
                raise PatchError('no_backup')
            journal, data = backups[0]
            return self._restore(game, journal, data, progress)
