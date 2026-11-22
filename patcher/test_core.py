"""Regression tests use temporary game installations; never write to real saves."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import core


class PatcherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.game = self.root / 'SteamLibrary/steamapps/common/ProjectZomboid'
        self.game.mkdir(parents=True)
        self.mods = self.root / 'player/Zomboid/mods'
        self.engine = core.Engine(storage=self.root / 'state', guard=lambda: None, mods=self.mods)
        self.put('projectzomboid.jar', b'fixture')
        self.put('ProjectZomboid64.exe', b'fixture')
        self.put('media/lua/shared/Translate/EN/Muldraugh, KY.json', b'{}')
        self.put(core.PRESET_PATH, ('-- header\r\nlocal OUTFITS_VERSION = 1\r\n' + self.engine.preset_before.replace('\n', '\r\n') + '\r\n-- footer\r\n').encode())
        for lang in ('EN', 'ID'):
            # Future author-provided translations must take precedence.
            labels = {'UI_original': 'Leave this intact', 'UI_ClothingType_ALICE:Tail': 'Existing author label'}
            self.put(f'media/lua/shared/Translate/{lang}/UI.json', json.dumps(labels).encode())
        self.put('Saves/Multiplayer/server/map/1703/512.bin', b'world never touched')
        self.put('Lua/saved_outfits.txt', b'VERSION=1\nKeep:KATTAJ1:BackFanny=Base.Bag|2;\n')
        self.original = self.snapshot()

    def put(self, relative, data):
        target = self.game / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    def snapshot(self):
        return {path.relative_to(self.game).as_posix(): path.read_bytes() for path in self.game.rglob('*') if path.is_file()}

    def mod_snapshot(self):
        return {path.relative_to(self.mods).as_posix(): path.read_bytes() for path in self.mods.rglob('*') if path.is_file()}

    def assert_error(self, code, function):
        with self.assertRaises(core.PatchError) as context:
            function()
        self.assertEqual(context.exception.code, code)

    def test_patch_verify_idempotent_and_restore(self):
        result = self.engine.apply(self.game)
        self.assertEqual(result['changed_files'], 234)
        self.assertEqual(result['counts']['viewpoint'], 6)
        self.assertEqual(len(self.mod_snapshot()), 6)
        self.assertTrue((self.mods / 'DerpyAutodriveViewpoint/common/mod.info').is_file())
        self.assertEqual(self.engine.plan(self.game)[0], [])
        patched = self.snapshot()
        for lang in ('EN', 'ID'):
            labels = json.loads(patched[f'media/lua/shared/Translate/{lang}/UI.json'])
            self.assertEqual(labels['UI_original'], 'Leave this intact')
            self.assertEqual(labels['UI_ClothingType_ALICE:Tail'], 'Existing author label')
            self.assertEqual(len(labels), 32)
        self.assertEqual(patched['Lua/saved_outfits.txt'], self.original['Lua/saved_outfits.txt'])
        self.assertEqual(patched['Saves/Multiplayer/server/map/1703/512.bin'], b'world never touched')
        self.assertEqual(self.engine.apply(self.game)['status'], 'already_patched')
        self.assertEqual(len(self.engine.backups(self.game)), 1)
        self.engine.restore(self.game)
        self.assertEqual(self.snapshot(), self.original)
        self.assertEqual(self.mod_snapshot(), {})
        self.assertEqual(self.engine.backups(self.game), [])

    def test_existing_local_addon_is_backed_up_and_restored(self):
        relative = 'DerpyAutodriveViewpoint/common/mod.info'
        existing = self.mods / relative
        existing.parent.mkdir(parents=True)
        existing.write_bytes(b'older local add-on')
        unrelated = self.mods / 'AnotherMod/common/mod.info'
        unrelated.parent.mkdir(parents=True)
        unrelated.write_bytes(b'unrelated mod')
        before = self.mod_snapshot()
        self.engine.apply(self.game)
        self.assertNotEqual(existing.read_bytes(), b'older local add-on')
        self.engine.restore(self.game)
        self.assertEqual(self.mod_snapshot(), before)

    def test_later_addon_update_blocks_entire_restore(self):
        self.engine.apply(self.game)
        jar = self.mods / 'DerpyAutodriveViewpoint/common/media/viewpoint/addons/derpy.autodrive-viewpoint/DerpyAutodriveViewpoint.jar'
        jar.write_bytes(b'newer add-on version')
        before_game, before_mods = self.snapshot(), self.mod_snapshot()
        self.assert_error('restore_conflict', lambda: self.engine.restore(self.game))
        self.assertEqual(self.snapshot(), before_game)
        self.assertEqual(self.mod_snapshot(), before_mods)

    def test_addon_write_failure_rolls_back_both_roots(self):
        write = self.engine.write_atomic
        calls = 0
        def failing(path, data):
            nonlocal calls
            if path.is_relative_to(self.mods):
                calls += 1
                if calls == 2:
                    raise OSError('simulated full mod disk')
            write(path, data)
        with patch.object(self.engine, 'write_atomic', side_effect=failing):
            self.assert_error('rolled_back', lambda: self.engine.apply(self.game))
        self.assertEqual(self.snapshot(), self.original)
        self.assertEqual(self.mod_snapshot(), {})

    def test_restore_refuses_different_player_mods_folder(self):
        self.engine.apply(self.game)
        self.engine.mods = (self.root / 'other-player/Zomboid/mods').resolve()
        before = self.snapshot()
        self.assert_error('backup_invalid', lambda: self.engine.restore(self.game))
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(self.engine.mods.exists())

    def test_missing_or_tampered_addon_payload_is_refused(self):
        import shutil
        payload = self.root / 'payload'
        shutil.copytree(self.engine.payload, payload)
        relative = next(iter(core.MOD_PATHS))
        (payload / relative).write_bytes(b'damaged payload')
        self.assert_error('payload_invalid', lambda: core.Engine(payload=payload, mods=self.mods))
        (payload / relative).unlink()
        self.assert_error('payload_invalid', lambda: core.Engine(payload=payload, mods=self.mods))
        manifest = json.loads((payload / 'manifest.json').read_text())
        del manifest['files'][relative]
        (payload / 'manifest.json').write_text(json.dumps(manifest))
        self.assert_error('payload_invalid', lambda: core.Engine(payload=payload, mods=self.mods))

    def test_mod_paths_remain_whitelisted(self):
        for path in ('local-mods/OtherMod/common/mod.info', 'local-mods/DerpyAutodriveViewpoint/../../Saves/player.db'):
            self.assert_error('unsafe_path', lambda: self.engine.target(self.game, path))

    def test_legacy_game_only_backup_restores_without_touching_addon(self):
        self.engine.apply(self.game)
        journal, data = self.engine.backups(self.game)[0]
        data['version'] = '1.0.0'
        del data['mods']
        data['entries'] = [entry for entry in data['entries'] if entry['path'] not in core.MOD_PATHS]
        self.engine.journal(journal, data)
        mods_before = self.mod_snapshot()
        self.engine.restore(self.game)
        self.assertEqual(self.snapshot(), self.original)
        self.assertEqual(self.mod_snapshot(), mods_before)

    def test_shared_mod_folder_is_locked_across_game_installations(self):
        other = core.Engine(storage=self.root / 'state', guard=lambda: None, mods=self.mods)
        with self.engine.lock(self.game):
            self.assert_error('another_patcher', lambda: other.apply(self.root / 'OtherGame'))

    def test_game_running_blocks_patch_and_restore(self):
        def blocked():
            raise core.PatchError('game_running')
        self.engine.guard = blocked
        self.assert_error('game_running', lambda: self.engine.apply(self.game))
        self.assertEqual(self.snapshot(), self.original)
        self.engine.guard = lambda: None
        self.engine.apply(self.game)
        patched = self.snapshot()
        self.engine.guard = blocked
        self.assert_error('game_running', lambda: self.engine.restore(self.game))
        self.assertEqual(self.snapshot(), patched)

    def test_unfamiliar_parser_blocks_every_change(self):
        self.put(core.PRESET_PATH, b'local OUTFITS_VERSION = 2\nnew reader')
        before = self.snapshot()
        self.assert_error('unknown_parser', lambda: self.engine.apply(self.game))
        self.assertEqual(self.snapshot(), before)

    def test_modified_reader_with_same_two_lines_is_refused(self):
        original = (self.game / core.PRESET_PATH).read_bytes()
        self.put(core.PRESET_PATH, original.replace(b'local retVal = {};', b'local retVal = {changed = true};'))
        before = self.snapshot()
        self.assert_error('unknown_parser', lambda: self.engine.apply(self.game))
        self.assertEqual(self.snapshot(), before)

    def test_restore_refuses_later_updates_before_any_restore(self):
        self.engine.apply(self.game)
        self.put(core.PRESET_PATH, b'new Steam update')
        patched = self.snapshot()
        self.assert_error('restore_conflict', lambda: self.engine.restore(self.game))
        self.assertEqual(self.snapshot(), patched)

    def test_failed_write_rolls_back(self):
        original_write = self.engine.write_atomic
        calls = 0
        def failing(path, data):
            nonlocal calls
            if path.is_relative_to(self.game):
                calls += 1
                if calls == 3:
                    raise OSError('simulated full disk')
            original_write(path, data)
        with patch.object(self.engine, 'write_atomic', side_effect=failing):
            self.assert_error('rolled_back', lambda: self.engine.apply(self.game))
        self.assertEqual(self.snapshot(), self.original)

    def test_launch_mid_patch_keeps_recoverable_backup(self):
        launched = False
        def guard():
            if launched:
                raise core.PatchError('game_running')
        def progress(*args):
            nonlocal launched
            launched = True
        self.engine.guard = guard
        self.assert_error('recovery_required', lambda: self.engine.apply(self.game, progress))
        self.assertEqual(self.engine.backups(self.game)[0][1]['status'], 'needs_recovery')
        self.engine.guard = lambda: None
        self.assert_error('recovery_required', lambda: self.engine.apply(self.game))
        self.engine.restore(self.game)
        self.assertEqual(self.snapshot(), self.original)

    def test_tampered_backup_cannot_restore_outside_game(self):
        self.engine.apply(self.game)
        journal, data = self.engine.backups(self.game)[0]
        data['entries'][0]['path'] = '../outside.txt'
        self.engine.journal(journal, data)
        before = self.snapshot()
        self.assert_error('unsafe_path', lambda: self.engine.restore(self.game))
        self.assertEqual(self.snapshot(), before)

    def test_detection_reads_secondary_library_and_manifest(self):
        steam = self.root / 'Steam'
        (steam / 'steamapps').mkdir(parents=True)
        library = self.game.parents[2]
        escaped = str(library).replace('\\', '\\\\')
        (steam / 'steamapps/libraryfolders.vdf').write_text('"libraryfolders" { "1" { "path" "' + escaped + '" "apps" { "108600" "123" } } }')
        (library / 'steamapps/appmanifest_108600.acf').write_text('"AppState" { "appid" "108600" "installdir" "ProjectZomboid" }')
        self.assertEqual(core.detect_games([steam]), [self.game.resolve()])
        (library / 'steamapps/appmanifest_108600.acf').write_text('"AppState" { "appid" "108600" "installdir" "../../escape" }')
        self.assertEqual(core.detect_games([steam]), [])

    def test_no_client_executable_refuses_dedicated_server(self):
        (self.game / 'ProjectZomboid64.exe').unlink()
        self.assert_error('wrong_folder', lambda: self.engine.apply(self.game))

    def test_process_detection_native_and_java(self):
        import psutil
        class Process:
            pid = 123
            def __init__(self, name, command=None, denied=False):
                self.info = {'name': name}
                self.command, self.denied = command or [], denied
            def cmdline(self):
                if self.denied:
                    raise psutil.AccessDenied(self.pid)
                return self.command
            def exe(self):
                return 'C:\\Java\\java.exe'
        for process in [Process('ProjectZomboid64.exe'), Process('java.exe', ['java', '-cp', 'projectzomboid.jar', 'zombie.gameStates.MainScreen'])]:
            with patch('psutil.process_iter', return_value=[process]):
                self.assertTrue(core.running_game_processes())
                self.assert_error('game_running', core.ensure_closed)
        with patch('psutil.process_iter', return_value=[Process('java.exe', ['java', '-jar', 'unrelated.jar'])]):
            self.assertEqual(core.running_game_processes(), [])
        with patch('psutil.process_iter', return_value=[Process('javaw.exe', denied=True)]):
            self.assert_error('process_unknown', core.ensure_closed)

    def test_operation_lock(self):
        with self.engine.lock(self.game):
            self.assert_error('another_patcher', lambda: self.engine.apply(self.game))


if __name__ == '__main__':
    unittest.main(verbosity=2)
