import io
import json
from pathlib import Path
import queue
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from PIL import Image

from app import STRINGS
from core import PatchError, sha
from mods_view import ModsTable, ThumbnailCache
from releases import ApprovedMods, CHANNEL


class ReleaseComparisonTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.files = {'zcp_123456_Demo/mod.info': b'id=Demo', 'zcp_123456_Demo/a.lua': b'first',
                      'zcp_654321_Other/mod.info': b'id=Other'}
        self.release = '100-aabbccddeeff'
        self.requests = []
        self.engine = ApprovedMods(self.root / 'Zomboid/mods', self.root / 'state', guard=lambda: None, opener=self.open)

    def tearDown(self): self.temp.cleanup()

    def manifest(self):
        entries = [{'path': p, 'size': len(b), 'sha256': sha(b)} for p, b in self.files.items()]
        mods = []
        for id_, name in [('123456', 'Demo mod'), ('654321', 'Other mod')]:
            item = [e for e in entries if e['path'].startswith('zcp_' + id_ + '_')]
            if item: mods.append({'workshopId': id_, 'title': name, 'revision': sha(json.dumps(item).encode()), 'modIds': []})
        return {'schema': 1, 'channel': CHANNEL, 'release': self.release, 'mods': mods, 'files': entries}

    def open(self, url):
        self.requests.append(url)
        if url.endswith('/latest'): return io.BytesIO(json.dumps(self.manifest()).encode())
        return io.BytesIO(next(b for b in self.files.values() if sha(b) == url.rsplit('/', 1)[1]))

    def test_missing_install_and_matching_versions_move_between_tabs_after_sync(self):
        missing = self.engine.inspect()
        self.assertEqual(missing['needs_update'], 2)
        self.assertTrue(all(r['state'] == 'missing' and r['client_revision'] is None for r in missing['rows']))
        self.assertFalse(self.engine.mods.exists())
        self.engine.sync()
        current = self.engine.inspect()
        self.assertEqual((current['needs_update'], current['current']), (0, 2))
        self.assertTrue(all(r['server_revision'] == r['client_revision'] for r in current['rows']))

    def test_hash_verification_detects_modification_and_missing_files_despite_same_recorded_version(self):
        self.engine.sync()
        (self.engine.mods / 'zcp_123456_Demo/a.lua').write_bytes(b'local modification')
        report = self.engine.inspect()
        self.assertEqual((report['needs_update'], report['current']), (1, 1))
        self.assertEqual(next(r for r in report['rows'] if r['workshop_id'] == '123456')['state'], 'modified')
        self.engine.sync()
        self.assertEqual(self.engine.inspect()['needs_update'], 0)
        self.engine.restore()
        self.assertEqual((self.engine.mods / 'zcp_123456_Demo/a.lua').read_bytes(), b'local modification')
        (self.engine.mods / 'zcp_123456_Demo/a.lua').unlink()
        self.assertEqual(self.engine.inspect()['needs_update'], 1)
        self.engine.sync()
        self.assertEqual(self.engine.inspect()['needs_update'], 0)

    def test_updated_release_has_independent_per_mod_versions_and_downloads_changed_files_only(self):
        self.engine.sync()
        self.release = '101-aabbccddeeff'; self.files['zcp_123456_Demo/a.lua'] = b'updated'
        report = self.engine.inspect()
        self.assertEqual((report['needs_update'], report['current']), (1, 1))
        updated = next(r for r in report['rows'] if r['state'] == 'outdated')
        self.assertNotEqual(updated['client_revision'], updated['server_revision'])
        self.requests.clear(); self.engine.sync()
        self.assertEqual(sum('/files/' in r for r in self.requests), 1)
        self.assertEqual(self.engine.inspect()['current'], 2)

    def test_no_approved_release_hides_local_history(self):
        self.engine.sync()
        self.engine.latest = lambda: None
        self.assertEqual(self.engine.inspect()['rows'], [])

    def test_foreign_existing_folder_is_never_adopted_or_overwritten_on_sync(self):
        foreign = self.engine.mods / 'zcp_123456_Demo/local.txt'
        foreign.parent.mkdir(parents=True); foreign.write_bytes(b'user')
        with self.assertRaises(PatchError): self.engine.sync()
        self.assertEqual(foreign.read_bytes(), b'user')

    def test_recovery_never_marks_files_latest(self):
        self.engine.sync(); self.engine.write(self.engine.pending, {})
        report = self.engine.inspect()
        self.assertTrue(report['recovery'])
        self.assertEqual(report['current'], 0)

    def test_comparison_cannot_query_steam_or_write_mod_files(self):
        self.engine.inspect()
        self.assertTrue(all(url.endswith('/latest') for url in self.requests))
        self.assertFalse(self.engine.mods.exists())

    def test_modified_older_copy_is_labelled_modified_and_failed_repair_restores_it(self):
        self.engine.sync()
        file = self.engine.mods / 'zcp_123456_Demo/a.lua'
        file.write_bytes(b'personal edit')
        self.release = '101-aabbccddeeff'; self.files['zcp_123456_Demo/a.lua'] = b'new server version'
        row = next(r for r in self.engine.inspect()['rows'] if r['workshop_id'] == '123456')
        self.assertEqual(row['state'], 'modified')
        import os
        replace = os.replace
        failed = False
        def fail_install(source, target):
            nonlocal failed
            if not failed and Path(source).name == 'zcp_123456_Demo' and 'new' in Path(source).parts:
                failed = True
                raise OSError('simulated install failure')
            return replace(source, target)
        with patch('releases.os.replace', side_effect=fail_install):
            with self.assertRaises(OSError): self.engine.sync()
        self.assertEqual(file.read_bytes(), b'personal edit')
        self.assertFalse(self.engine.pending.exists())


class ThumbnailTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        data = io.BytesIO(); Image.new('RGB', (160, 100), '#abcdef').save(data, format='JPEG')
        self.data = data.getvalue()
    def tearDown(self): self.temp.cleanup()

    def test_jpeg_thumbnail_decodes_and_is_cached_as_small_png(self):
        calls = []
        def open_(url): calls.append(url); return io.BytesIO(self.data)
        cache = ThumbnailCache(self.temp.name, open_)
        first = cache.get('123456')
        self.assertEqual(Image.open(io.BytesIO(first)).size, (44, 44))
        self.assertEqual(first, cache.get('123456'))
        self.assertEqual(len(calls), 1)

    def test_invalid_images_and_ids_have_safe_fallback(self):
        cache = ThumbnailCache(self.temp.name, lambda _: io.BytesIO(b'not an image'))
        self.assertIsNone(cache.get('123456')); self.assertIsNone(cache.get('../escape'))
        self.assertIsNone(ThumbnailCache(self.temp.name, lambda _: io.BytesIO(b'x' * (2 * 1024 ** 2 + 1))).get('123456'))


class ModsTableTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk(); self.root.withdraw()
        self.messages = queue.Queue()
        self.language = 'en'
        translate = lambda key, **values: STRINGS[self.language][key].format(**values)
        def button(parent, key, command, primary=False): return tk.Button(parent, text=translate(key), command=command)
        cache = type('Cache', (), {'get': lambda _, id_: None})()
        self.view = ModsTable(self.root, translate, button, lambda: None, self.messages, cache)
        self.view.pack(); self.root.update_idletasks()
    def tearDown(self): self.view.close(); self.root.destroy()

    def report(self, current=False):
        return {'latest': '100-aabbccddeeff', 'installed': '100-aabbccddeeff' if current else None, 'recovery': False,
                'needs_update': 0 if current else 1, 'current': 1 if current else 0,
                'rows': [{'workshop_id': '123456', 'title': 'Demo mod', 'server_revision': 'a' * 64,
                          'client_revision': 'a' * 64 if current else None, 'state': 'current' if current else 'missing', 'present': current}]}

    def test_tabs_columns_and_one_sync_action(self):
        self.view.set_report(self.report())
        self.assertEqual(self.view.book.tab(0, 'text'), 'Needs Update (1)')
        self.assertEqual(self.view.book.tab(1, 'text'), 'Latest (0)')
        self.assertEqual(self.view.trees['needs'].heading('server')['text'], 'Server Mod Version')
        self.assertEqual(self.view.trees['needs'].item('123456')['values'][1], 'Not installed')
        self.assertEqual(str(self.view.sync_button.master), str(self.view.frames['needs']))
        self.assertEqual(self.view.sync_button.cget('text'), 'Sync/Patch Mods from Server')
        self.assertTrue(self.view.can_sync)
        self.assertFalse(self.view.can_play)

    def test_success_moves_row_to_latest_and_disables_sync(self):
        self.view.set_report(self.report()); self.view.set_report(self.report(True))
        self.assertEqual(self.view.trees['needs'].get_children(), ())
        self.assertEqual(self.view.trees['latest'].get_children(), ('123456',))
        self.assertEqual(self.view.book.select(), str(self.view.frames['latest']))
        self.assertFalse(self.view.can_sync); self.assertTrue(self.view.can_play)

    def test_failed_or_running_checks_disable_sync_and_language_refreshes_headings(self):
        self.view.set_report(self.report()); self.view.begin(); self.assertFalse(self.view.can_sync)
        self.view.failed(); self.assertFalse(self.view.can_sync)
        self.language = 'id'; self.view.render()
        self.assertEqual(self.view.book.tab(0, 'text'), 'Perlu Update (1)')
        self.assertEqual(self.view.trees['needs'].heading('client')['text'], 'Versi Mod Client')


if __name__ == '__main__': unittest.main()
