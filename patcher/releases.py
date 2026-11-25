"""Approved server releases. Only zcp_<WorkshopID>_* local mod folders are managed."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

from core import Engine, PatchError, ensure_closed, sha, state_dir, steam_roots, validate_game

CHANNEL = '9059cf4f988a72fe963e87c8'
BASE_URL = 'https://pz.12washere.pro/api/mod-releases'
MAX_MANIFEST = 64 * 1024 ** 2
MAX_FILE = 2 * 1024 ** 3


def relative(value):
    if not isinstance(value, str) or not value or len(value) > 220 or re.search(r'[\\:\x00-\x1f<>"|?*]', value):
        raise PatchError('unsafe_path', str(value))
    parts = value.split('/')
    if any(not p or p in ('.', '..') or p.endswith(('.', ' ')) or re.match(r'^(con|prn|aux|nul|com[0-9]|lpt[0-9])(?:\.|$)', p, re.I) for p in parts):
        raise PatchError('unsafe_path', value)
    if len(parts) < 2 or not re.fullmatch(r'zcp_[0-9]{1,15}_[^/]+', parts[0]):
        raise PatchError('unsafe_path', value)
    return value


def validate_manifest(data, channel):
    if not isinstance(data, dict) or data.get('schema') != 1 or data.get('channel') != channel or not re.fullmatch(r'[0-9]+-[a-f0-9]{12}', str(data.get('release', ''))):
        raise PatchError('release_invalid', 'Unrecognized approved release manifest.')
    files = data.get('files')
    if not isinstance(files, list) or len(files) > 250000:
        raise PatchError('release_invalid', 'Invalid file list.')
    seen, total = set(), 0
    for item in files:
        if not isinstance(item, dict):
            raise PatchError('release_invalid')
        name = relative(item.get('path')).casefold()
        if name in seen or type(item.get('size')) is not int or not 0 <= item['size'] <= MAX_FILE or not re.fullmatch('[a-f0-9]{64}', str(item.get('sha256', ''))):
            raise PatchError('release_invalid', 'Invalid or duplicate release file.')
        seen.add(name)
        total += item['size']
    if total > 100 * 1024 ** 3:
        raise PatchError('release_invalid', 'Release exceeds 100 GB.')
    for name in seen:
        if any('/'.join(name.split('/')[:i]) in seen for i in range(1, len(name.split('/')))):
            raise PatchError('release_invalid', 'A release file is also a directory.')
    return data


class SameOriginRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urllib.parse.urlsplit(newurl)[:2] != urllib.parse.urlsplit(req.full_url)[:2]:
            raise PatchError('release_invalid', 'Release download redirected to another host.')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def open_url(url):
    return urllib.request.build_opener(SameOriginRedirect()).open(
        urllib.request.Request(url, headers={'User-Agent': '12washere.pro-Patcher', 'Accept-Encoding': 'identity'}), timeout=45)


class ApprovedMods:
    def __init__(self, mods=None, storage=None, guard=None, opener=None, channel=CHANNEL):
        if not re.fullmatch('[a-f0-9]{24}', channel):
            raise PatchError('release_invalid', 'Invalid release channel.')
        self.mods = Path(mods or Path.home() / 'Zomboid/mods').absolute()
        self.storage = Path(storage or state_dir()).resolve()
        self.guard = guard or ensure_closed
        self.open = opener or open_url
        self.channel = channel
        key = sha(str(self.mods).casefold().encode())[:16]
        self.directory = self.storage / 'approved-mods' / key / channel
        self.state_file = self.directory / 'installed.json'
        self.pending = self.directory / 'pending.json'
        self.work_root = self.mods.parent / '.12washere-release-backups' / channel
        self.lock_dir = self.storage / 'locks' / ('mods-' + key)

    def write(self, file, data):
        Engine.write_atomic(file, (json.dumps(data, indent=2) + '\n').encode())

    def read_state(self):
        if not self.state_file.exists():
            return None
        data = json.loads(self.state_file.read_text(encoding='utf-8'))
        validate_manifest(data['manifest'], self.channel)
        return data

    def latest(self):
        url = f'{BASE_URL}/{self.channel}/latest'
        try:
            with self.open(url) as response:
                raw = response.read(MAX_MANIFEST + 1)
            if len(raw) > MAX_MANIFEST:
                raise PatchError('release_invalid', 'Release manifest is too large.')
            return validate_manifest(json.loads(raw), self.channel)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                exc.close()
                return None
            raise PatchError('release_network', str(exc)) from exc
        except (OSError, ValueError) as exc:
            raise PatchError('release_network', str(exc)) from exc

    def target(self, name):
        relative(name)
        self.check_links(self.mods)
        target = self.mods / name
        self.check_links(target)
        if not target.resolve().is_relative_to(self.mods.resolve()):
            raise PatchError('unsafe_path', name)
        return target

    @staticmethod
    def check_links(file):
        for parent in (file, *file.parents):
            if parent.is_symlink() or (hasattr(parent, 'is_junction') and parent.is_junction()):
                raise PatchError('unsafe_path', 'Symlink/junction in release installation path.')

    @staticmethod
    def digest(file):
        with file.open('rb') as stream:
            return hashlib.file_digest(stream, 'sha256').hexdigest()

    def actual(self, root, base=None):
        base = base or self.mods
        folder = base / root
        self.check_links(folder)
        if not folder.exists():
            return {}
        if not folder.is_dir():
            raise PatchError('release_conflict', root)
        result = {}
        for parent, directories, files in os.walk(folder, followlinks=False):
            for name in directories + files:
                self.check_links(Path(parent) / name)
            for name in files:
                file = Path(parent) / name
                rel = file.relative_to(base).as_posix()
                relative(rel)
                if not file.is_file():
                    raise PatchError('unsafe_path', rel)
                result[rel] = self.digest(file)
        return result

    @staticmethod
    def inventory(manifest):
        result = {}
        for item in manifest['files']:
            result.setdefault(item['path'].split('/')[0], {})[item['path']] = item['sha256']
        return result

    def status(self):
        latest, installed = self.latest(), self.read_state()
        return {'latest': latest['release'] if latest else None,
                'installed': installed['manifest']['release'] if installed else None,
                'mods': len(latest.get('mods', [])) if latest else 0,
                'bytes': sum(f['size'] for f in latest['files']) if latest else 0,
                'recovery': self.pending.exists()}

    def check_duplicates(self, manifest):
        ids = {id_ for mod in manifest.get('mods', []) for id_ in mod.get('modIds', [])}
        managed = set(self.inventory(manifest))
        if not self.mods.exists() or not ids:
            return
        for folder in self.mods.iterdir():
            self.check_links(folder)
            if not folder.is_dir() or folder.name in managed:
                continue
            for info in [folder / 'mod.info', *folder.glob('*/mod.info')]:
                if not info.is_file(): continue
                self.check_links(info)
                if info.stat().st_size > 65536: continue
                for line in info.read_text(encoding='utf-8-sig', errors='replace').splitlines():
                    key, separator, value = line.partition('=')
                    if separator and key.strip().lower() == 'id' and value.strip() in ids:
                        raise PatchError('release_conflict', f'{folder.name} provides duplicate Mod ID {value.strip()}. Back up and move that older local copy out of Zomboid/mods.')

    def download(self, manifest, file, progress):
        cache = self.directory / 'cache' / file['sha256']
        if cache.is_file() and cache.stat().st_size == file['size'] and self.digest(cache) == file['sha256']:
            return cache
        cache.parent.mkdir(parents=True, exist_ok=True)
        temporary = cache.with_suffix('.' + uuid.uuid4().hex + '.part')
        try:
            with self.open(f"{BASE_URL}/{self.channel}/{manifest['release']}/files/{file['sha256']}") as stream, temporary.open('wb') as output:
                remaining = file['size']
                digest = hashlib.sha256()
                while remaining:
                    chunk = stream.read(min(1024 ** 2, remaining))
                    if not chunk:
                        raise PatchError('release_invalid', 'Download ended before the declared file size.')
                    remaining -= len(chunk)
                    output.write(chunk)
                    digest.update(chunk)
                    progress(len(chunk))
                if stream.read(1) or digest.hexdigest() != file['sha256']:
                    raise PatchError('release_invalid', 'Downloaded mod file failed size/hash verification.')
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, cache)
        except (OSError, urllib.error.URLError) as exc:
            raise PatchError('release_network', str(exc)) from exc
        finally:
            temporary.unlink(missing_ok=True)
        return cache

    def sync(self, progress=lambda *_: None):
        with Engine._lock_file(self, self.lock_dir):
            self.guard()
            if self.pending.exists():
                raise PatchError('recovery_required', 'Use Restore mod release to recover the interrupted update.')
            latest = self.latest()
            if latest is None:
                return {'status': 'no_release'}
            self.check_duplicates(latest)
            installed = self.read_state()
            previous = installed['manifest'] if installed else {'files': []}
            before, after = self.inventory(previous), self.inventory(latest)
            roots = sorted(set(before) | set(after))
            actual = {root: self.actual(root) for root in roots}
            if actual == {root: after.get(root, {}) for root in roots}:
                self.write(self.state_file, {**(installed or {}), 'manifest': latest})
                return {'status': 'current', 'release': latest['release']}
            changed = [root for root in roots if actual[root] != after.get(root, {})]
            for root in changed:
                if actual[root] != before.get(root, {}) or (root not in before and (self.mods / root).exists()):
                    raise PatchError('release_conflict', f'{root} contains files outside the previously installed release. Back up/move that folder before syncing.')
            total, done = sum(f['size'] for f in latest['files'] if f['path'].split('/')[0] in changed), 0
            progress_lock = Lock()
            def tick(amount):
                nonlocal done
                with progress_lock:
                    done += amount
                    progress(done, max(total, 1), 'Approved server mods')
            self.mods.mkdir(parents=True, exist_ok=True)
            self.check_links(self.work_root)
            work = self.work_root / uuid.uuid4().hex
            work.mkdir(parents=True)
            needed = {file['sha256']: file for file in latest['files']
                      if file['path'].split('/')[0] in changed
                      and actual[file['path'].split('/')[0]].get(file['path']) != file['sha256']}
            with ThreadPoolExecutor(max_workers=8) as pool:
                futures = {key: pool.submit(self.download, latest, file, tick) for key, file in needed.items()}
                downloaded = {key: future.result() for key, future in futures.items()}
            for file in latest['files']:
                root = file['path'].split('/')[0]
                if root not in changed:
                    continue
                target = work / 'new' / file['path']
                target.parent.mkdir(parents=True, exist_ok=True)
                # Unchanged files are reused directly from the verified local copy.
                if actual[root].get(file['path']) == file['sha256']:
                    source = self.target(file['path'])
                else:
                    source = downloaded[file['sha256']]
                shutil.copyfile(source, target)
                if self.digest(target) != file['sha256']:
                    raise PatchError('release_invalid', 'Mod files changed during staging.')
            self.guard()  # The player may have opened PZ during a long download.
            if any(self.actual(root) != actual[root] for root in roots):
                raise PatchError('files_changed', 'Local mods changed during the download.')
            if shutil.disk_usage(self.mods).free < 64 * 1024 ** 2:
                raise PatchError('release_invalid', 'Less than 64 MB free disk space remains.')
            transaction = {'work': str(work), 'roots': changed, 'moved': [], 'installed': [],
                           'previous': {'manifest': installed['manifest']} if installed else None, 'manifest': latest}
            self.write(self.pending, transaction)
            try:
                for root in changed:
                    if (self.mods / root).exists():
                        (work / 'old').mkdir(exist_ok=True)
                        transaction['moved'].append(root); self.write(self.pending, transaction)
                        os.replace(self.mods / root, work / 'old' / root)
                    if (work / 'new' / root).exists():
                        transaction['installed'].append(root); self.write(self.pending, transaction)
                        os.replace(work / 'new' / root, self.mods / root)
                if any(self.actual(root) != after.get(root, {}) for root in roots):
                    raise PatchError('verification_failed')
                self.write(self.state_file, {'manifest': latest, 'backup': transaction})
                self.pending.unlink()
            except Exception:
                self._recover(transaction)
                raise
            return {'status': 'installed', 'release': latest['release'], 'folders': len(changed)}

    def _work(self, transaction):
        work = Path(transaction['work'])
        self.check_links(work)
        if work.parent != self.work_root or not re.fullmatch('[a-f0-9]{32}', work.name):
            raise PatchError('backup_invalid')
        for root in transaction['roots']:
            relative(root + '/placeholder')
        if any(r not in transaction['roots'] for r in transaction['moved'] + transaction['installed']):
            raise PatchError('backup_invalid')
        return work

    def _recover(self, transaction):
        work = self._work(transaction)
        previous = self.inventory(transaction['previous']['manifest']) if transaction['previous'] else {}
        after = self.inventory(transaction['manifest'])
        # Validate every backup before deleting anything. A retry after a crash
        # between restoring a folder and removing the journal is idempotent.
        for root in transaction['moved']:
            backup_exists = (work / 'old' / root).exists()
            actual = self.actual(root, work / 'old') if backup_exists else self.actual(root)
            if actual != previous.get(root, {}):
                raise PatchError('backup_invalid', root)
        for root in reversed(transaction['roots']):
            backup = work / 'old' / root
            target = self.mods / root
            if backup.exists():
                current = self.actual(root)
                if current and current != after.get(root, {}):
                    raise PatchError('restore_conflict', root)
                if target.exists(): shutil.rmtree(target)
                os.replace(backup, target)
            elif root not in transaction['moved'] and root in transaction['installed'] and not (work / 'new' / root).exists():
                if self.actual(root) != after.get(root, {}) and target.exists():
                    raise PatchError('restore_conflict', root)
                if target.exists(): shutil.rmtree(target)
        if transaction['previous']:
            self.write(self.state_file, transaction['previous'])
        else:
            self.state_file.unlink(missing_ok=True)
        self.pending.unlink(missing_ok=True)

    def restore(self):
        with Engine._lock_file(self, self.lock_dir):
            self.guard()
            if self.pending.exists():
                transaction = json.loads(self.pending.read_text(encoding='utf-8'))
                self._recover(transaction)
                return {'status': 'recovered'}
            installed = self.read_state()
            if not installed or not installed.get('backup'):
                raise PatchError('no_backup')
            transaction = installed['backup']
            work = self._work(transaction)
            after = self.inventory(installed['manifest'])
            previous = self.inventory(transaction['previous']['manifest']) if transaction['previous'] else {}
            for root in transaction['moved']:
                if self.actual(root, work / 'old') != previous.get(root, {}):
                    raise PatchError('backup_invalid', root)
            for root in transaction['roots']:
                if self.actual(root) != after.get(root, {}):
                    raise PatchError('restore_conflict', root)
            # Journal restoration too; moving the installed copy back to new/
            # makes _recover idempotent after a crash between folder operations.
            self.write(self.pending, transaction)
            for root in transaction['installed']:
                if (self.mods / root).exists():
                    (work / 'new').mkdir(exist_ok=True)
                    os.replace(self.mods / root, work / 'new' / root)
            self._recover(transaction)
            return {'status': 'restored'}

    def launch(self, game):
        validate_game(game)
        self.guard()
        if self.pending.exists():
            raise PatchError('recovery_required')
        latest, installed = self.latest(), self.read_state()
        if not latest or not installed or installed['manifest']['release'] != latest['release']:
            raise PatchError('release_outdated', 'Sync the approved release before launching.')
        expected = self.inventory(latest)
        self.check_duplicates(latest)
        if any(self.actual(root) != files for root, files in expected.items()):
            raise PatchError('release_conflict', 'Approved mod files changed. Sync or restore them first.')
        for steam in steam_roots():
            exe = steam / 'Steam.exe'
            if exe.is_file():
                subprocess.Popen([str(exe), '-applaunch', '108600', '-modfolders', 'mods,steam,workshop'], cwd=steam)
                return {'status': 'launched', 'release': latest['release']}
        raise PatchError('release_network', 'Steam.exe could not be found. Set Steam launch options to: -modfolders mods,steam,workshop')
