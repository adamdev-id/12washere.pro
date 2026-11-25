import io
import json
from pathlib import Path
import tempfile
import unittest
import urllib.error
from unittest.mock import patch

from core import PatchError, sha
from releases import ApprovedMods, CHANNEL, validate_manifest


class ApprovedReleasesTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.files = {'zcp_123456_Demo/common/mod.info': b'id=Demo', 'zcp_123456_Demo/file.lua': b'original'}
        self.release = '100-aabbccddeeff'
        self.requests = []
        self.engine = ApprovedMods(self.root / 'Zomboid/mods', self.root / 'state', guard=lambda: None, opener=self.open)

    def tearDown(self):
        self.temp.cleanup()

    def manifest(self):
        return {'schema': 1, 'channel': CHANNEL, 'release': self.release, 'mods': [{'workshopId': '123456'}],
                'files': [{'path': name, 'sha256': sha(data), 'size': len(data)} for name, data in self.files.items()]}

    def open(self, url):
        self.requests.append(url)
        if url.endswith('/latest'):
            return io.BytesIO(json.dumps(self.manifest()).encode())
        key = url.rsplit('/', 1)[1]
        return io.BytesIO(next(data for data in self.files.values() if sha(data) == key))

    def test_install_update_delete_obsolete_restore(self):
        self.assertEqual(self.engine.sync()['status'], 'installed')
        self.assertEqual(self.engine.sync()['status'], 'current')
        self.files = {'zcp_123456_Demo/common/mod.info': b'id=Demo', 'zcp_123456_Demo/new.lua': b'new'}
        self.release = '101-aabbccddeeff'
        self.requests.clear()
        self.engine.sync()
        self.assertFalse((self.engine.mods / 'zcp_123456_Demo/file.lua').exists())
        self.assertEqual(sum('/files/' in url for url in self.requests), 1)
        self.engine.restore()
        self.assertEqual((self.engine.mods / 'zcp_123456_Demo/file.lua').read_bytes(), b'original')
        self.assertFalse((self.engine.mods / 'zcp_123456_Demo/new.lua').exists())

    def test_no_release_is_no_op(self):
        self.engine.open = lambda url: (_ for _ in ()).throw(urllib.error.HTTPError(url, 404, '', {}, None))
        self.assertEqual(self.engine.sync()['status'], 'no_release')
        self.assertFalse(self.engine.mods.exists())

    def test_never_writes_unverified_download(self):
        self.engine.open = lambda url: io.BytesIO(json.dumps(self.manifest()).encode()) if url.endswith('/latest') else io.BytesIO(b'corrupted')
        with self.assertRaises(PatchError):
            self.engine.sync()
        self.assertFalse((self.engine.mods / 'zcp_123456_Demo').exists())

    def test_owned_user_changes_are_backed_up_and_restore_recovers_them(self):
        self.engine.sync()
        extra = self.engine.mods / 'zcp_123456_Demo/personal.lua'
        extra.write_bytes(b'user edit')
        self.release = '102-aabbccddeeff'
        self.files['zcp_123456_Demo/file.lua'] = b'update'
        self.engine.sync()
        self.assertFalse(extra.exists())
        self.engine.restore()
        self.assertEqual(extra.read_bytes(), b'user edit')

    def test_rollback_on_install_failure(self):
        self.engine.sync()
        self.release = '102-aabbccddeeff'
        self.files['zcp_123456_Demo/file.lua'] = b'update'
        import os
        real_replace = os.replace
        failed = False
        def replace(from_, to):
            nonlocal failed
            if Path(from_).name == 'zcp_123456_Demo' and 'new' in Path(from_).parts and not failed:
                failed = True
                raise OSError('simulated install failure')
            return real_replace(from_, to)
        with patch('releases.os.replace', side_effect=replace):
            with self.assertRaises(OSError): self.engine.sync()
        self.assertEqual((self.engine.mods / 'zcp_123456_Demo/file.lua').read_bytes(), b'original')
        self.assertFalse(self.engine.pending.exists())

    def test_process_guard_rechecks_after_download(self):
        count = 0
        def guard():
            nonlocal count
            count += 1
            if count > 1: raise PatchError('game_running')
        self.engine.guard = guard
        with self.assertRaises(PatchError): self.engine.sync()
        self.assertFalse((self.engine.mods / 'zcp_123456_Demo').exists())

    def test_identical_preinstalled_release_is_recorded(self):
        for name, data in self.files.items():
            file = self.engine.mods / name
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(data)
        self.assertEqual(self.engine.sync()['status'], 'current')
        self.files['zcp_123456_Demo/file.lua'] = b'updated'
        self.release = '103-aabbccddeeff'
        self.assertEqual(self.engine.sync()['status'], 'installed')

    def test_paths_duplicate_case_and_wrong_channel(self):
        for name in ['../outside', 'zcp_1_Demo/../../outside', 'zcp_1_Demo/CON', 'zcp_1_Demo/file.', 'zcp_1_Demo/C:\\out', 'OtherMod/file.lua']:
            manifest = self.manifest(); manifest['files'][0]['path'] = name
            with self.subTest(name=name), self.assertRaises(PatchError): validate_manifest(manifest, CHANNEL)
        manifest = self.manifest(); manifest['files'].append({**manifest['files'][0], 'path': manifest['files'][0]['path'].upper()})
        with self.assertRaises(PatchError): validate_manifest(manifest, CHANNEL)
        with self.assertRaises(PatchError): validate_manifest(self.manifest(), '0' * 24)

    def test_restore_checks_backup_before_changing_installed_mods(self):
        self.engine.sync()
        self.files['zcp_123456_Demo/file.lua'] = b'updated'
        self.release = '104-aabbccddeeff'
        self.engine.sync()
        state = self.engine.read_state()
        backup = Path(state['backup']['work']) / 'old/zcp_123456_Demo/file.lua'
        backup.write_bytes(b'corrupt backup')
        with self.assertRaises(PatchError): self.engine.restore()
        self.assertEqual((self.engine.mods / 'zcp_123456_Demo/file.lua').read_bytes(), b'updated')

    def test_retry_recovery_does_not_delete_already_restored_originals(self):
        self.engine.sync()
        self.files['zcp_123456_Demo/file.lua'] = b'updated'
        self.release = '104-aabbccddeeff'
        self.engine.sync()
        transaction = self.engine.read_state()['backup']
        self.engine._recover(transaction)
        self.engine._recover(transaction)
        self.assertEqual((self.engine.mods / 'zcp_123456_Demo/file.lua').read_bytes(), b'original')

    def test_duplicate_unmanaged_local_mod_id_is_refused(self):
        self.manifest = lambda: {'schema': 1, 'channel': CHANNEL, 'release': self.release,
            'mods': [{'modIds': ['Demo']}], 'files': [{'path': name, 'sha256': sha(data), 'size': len(data)} for name, data in self.files.items()]}
        other = self.engine.mods / 'OlderDemo/common/mod.info'
        other.parent.mkdir(parents=True)
        other.write_text('id=Demo')
        with self.assertRaises(PatchError): self.engine.sync()
        self.assertTrue(other.exists())


if __name__ == '__main__': unittest.main()
