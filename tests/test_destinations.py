import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tests.stubs import Player, install, make_main
install()
from endstone_utp.functions.home import Home
from endstone_utp.functions.warp import Warp


class DestinationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.main = make_main(self.temp.name)
        self.main.config_funct = SimpleNamespace(config_data={
            'max_home': 5, 'is_enabled': {'home': True, 'warp': True}})
        self.player = Player(admin=True)
        self.player.dimension = self.player.location.dimension
        self.home = Home(self.main)
        self.warp = Warp(self.main)

    def add(self, owner, kind, name):
        getattr(owner, f'_{kind.title()}__add_{kind}')(self.player)
        self.player.forms[-1].on_submit(self.player, json.dumps([name]))

    def test_online_player_without_join_can_open_and_add_home(self):
        self.home.home_main(self.player)
        self.add(self.home, 'home', '家')
        self.assertIn('家', json.loads((Path(self.temp.name)/'home.json').read_text())['Alice'])

    def test_write_failure_preserves_memory_and_bytes_and_no_success(self):
        for owner, kind in ((self.home, 'home'), (self.warp, 'warp')):
            with self.subTest(kind=kind):
                self.add(owner, kind, 'old')
                path = Path(self.temp.name)/f'{kind}.json'
                before, memory = path.read_bytes(), deepcopy(getattr(owner, f'_{kind.title()}__{kind}_data'))
                for operation in ('os.replace', 'os.fsync'):
                    with patch('endstone_utp.storage.' + operation, side_effect=OSError('disk full')):
                        self.add(owner, kind, 'new')
                    self.assertEqual(path.read_bytes(), before)
                    self.assertEqual(getattr(owner, f'_{kind.title()}__{kind}_data'), memory)
                    self.assertIn('保存失败', self.player.messages[-1])
                self.assertEqual(list(Path(self.temp.name).glob('.*.json.*')), [])

    def test_revoked_operator_and_disabled_feature_reject_open_forms(self):
        self.warp._Warp__add_warp(self.player)
        form = self.player.forms[-1]
        self.player.is_op = False
        form.on_submit(self.player, '["denied"]')
        self.assertEqual(self.warp._Warp__warp_data, {})
        self.player.is_op = True
        for owner, kind in ((self.home, 'home'), (self.warp, 'warp')):
            getattr(owner, f'_{kind.title()}__add_{kind}')(self.player)
            form = self.player.forms[-1]
            self.main.config_funct.config_data['is_enabled'][kind] = False
            form.on_submit(self.player, '["disabled"]')
            self.assertEqual(getattr(owner, f'_{kind.title()}__{kind}_data'), {})

    def test_rename_location_delete_and_recreate_invalidate_stale_actions(self):
        for owner, kind in ((self.home, 'home'), (self.warp, 'warp')):
            with self.subTest(kind=kind):
                prefix = f'_{kind.title()}__'
                self.add(owner, kind, 'old')
                getattr(owner, prefix+f'update_{kind}_name')('old', 'Overworld', [1,64,2])(self.player)
                rename = self.player.forms[-1]
                teleport = getattr(owner, prefix+f'{kind}_teleport')('old', 'Overworld', [1,64,2])
                delete = getattr(owner, prefix+f'delete_{kind}_c')('old')
                getattr(owner, prefix+f'update_{kind}_loc_c')('old', [9,80,9])(self.player)
                rename.on_submit(self.player, '["new"]')
                delete(self.player)
                data = getattr(owner, prefix+f'{kind}_data')
                records = data['Alice'] if kind == 'home' else data
                self.assertEqual(records['old']['loc'], [9,80,9])
                self.assertNotIn('new', records)
                getattr(owner, prefix+f'delete_{kind}_c')('old')(self.player)
                self.add(owner, kind, 'old')
                self.player.teleport = lambda location: self.fail('Stale teleport executed')
                teleport(self.player)

    def test_command_permission_revocation_blocks_existing_form(self):
        self.home._Home__add_home(self.player)
        form = self.player.forms[-1]
        self.player.command_allowed = False
        form.on_submit(self.player, '["denied"]')
        self.assertEqual(self.home._Home__home_data, {})

    def test_disabled_or_replaced_instance_cannot_commit_old_form(self):
        self.home._Home__add_home(self.player)
        form = self.player.forms[-1]
        self.main.is_enabled = False
        form.on_submit(self.player, '["disabled"]')
        self.assertEqual(self.home._Home__home_data, {})
        self.main.is_enabled = True
        self.main.home_funct = Home(self.main)
        form.on_submit(self.player, '["old generation"]')
        self.assertEqual(self.home._Home__home_data, {})

    def test_external_edits_are_not_overwritten(self):
        path = Path(self.temp.name)/'warp.json'
        path.write_text('{"external":{"dim":"Overworld","loc":[0,0,0]}}')
        before = path.read_bytes()
        self.add(self.warp, 'warp', 'new')
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(self.warp._Warp__warp_data, {})

    def test_invalid_existing_data_is_preserved(self):
        for kind, cls in (('home', Home), ('warp', Warp)):
            path = Path(self.temp.name)/f'{kind}.json'
            for raw in (b'{', b'[]', b'{"bad":42}'):
                path.write_bytes(raw)
                with self.assertRaises(ValueError):
                    cls(self.main)
                self.assertEqual(path.read_bytes(), raw)

    def test_delete_uses_message_and_cancelled_teleport_has_no_success(self):
        self.add(self.warp, 'warp', 'old')
        self.main.server.level = SimpleNamespace(get_dimension=lambda name: name)
        self.player.teleport = lambda location: False
        with patch('endstone_utp.functions.warp.Location', lambda *a, **kw: kw):
            self.warp._Warp__warp_teleport('old', 'Overworld', [1,64,2])(self.player)
        self.assertEqual(self.player.messages[-1], '传送被取消。')
        self.player.send_form = lambda form: self.fail('Deletion sent a form')
        self.warp._Warp__delete_warp_c('old')(self.player)
        self.assertIn('delete_warp.message.success', self.player.messages[-1])
