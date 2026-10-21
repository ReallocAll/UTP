"""Persistence safety checks; Endstone forms/events are synthetic test boundaries."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from tests.stubs import install

install()

from endstone_utp.functions.tpa import TPA


class FakePlayer:
    def __init__(self, name, *, is_op=False, locale="en_US", xuid=None):
        self.name = name
        self.xuid = xuid or f"xuid-{name}"
        self.locale = locale
        self.is_op = is_op
        self.messages = []
        self.forms = []
        self.teleports = []

    def send_message(self, message):
        self.messages.append(message)

    def send_form(self, form):
        self.forms.append(form)

    def teleport(self, target):
        self.teleports.append(target.name)


class FakeForm:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.buttons = []

    def add_button(self, text, **kwargs):
        self.buttons.append({"text": text, **kwargs})


class TPAPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.path = Path(self.tempdir.name) / "tpa_setting.json"
        self.sender = FakePlayer("Alice")
        self.acceptor = FakePlayer("Bob")
        players = [self.sender, self.acceptor]
        self.main = SimpleNamespace(
            first_dir_path=self.tempdir.name,
            logger=Mock(),
            server=SimpleNamespace(
                online_players=players,
                get_player=lambda name: next((p for p in players if p.name == name), None),
            ),
            back_to_main_form=Mock(),
        )
        for name in ("ActionForm", "ModalForm", "Dropdown", "TextInput"):
            patcher = patch(f"endstone_utp.functions.tpa.{name}", FakeForm)
            patcher.start()
            self.addCleanup(patcher.stop)

    def write_settings(self, value):
        self.path.write_text(json.dumps(value), encoding="utf-8")

    def assert_unavailable(self, tpa, original):
        tpa.on_player_join(SimpleNamespace(player=self.sender))
        tpa.settings_main(self.sender)
        tpa.tpa_main(self.sender)
        self.assertIsNone(tpa._TPA__tpa_setting_data)
        self.assertFalse(tpa._TPA__request_allowed("Alice", "Bob"))
        self.assertFalse(tpa._TPA__is_whitelisted("Alice", "Bob"))
        self.assertFalse(tpa._TPA__save_tpa_setting_data())
        self.assertEqual(self.path.read_bytes(), original)
        self.assertEqual(self.sender.forms, [])
        self.assertTrue(any("unavailable" in text for text in self.sender.messages))
        self.main.logger.error.assert_called()
        log = self.main.logger.error.call_args.args[0]
        self.assertIn(str(self.path), log)
        self.assertIn("restart", log)

    def test_missing_file_initializes_and_join_adds_real_player(self):
        tpa = TPA(self.main)
        self.assertEqual(json.loads(self.path.read_text()), {})
        tpa.on_player_join(SimpleNamespace(player=self.sender))
        self.assertEqual(json.loads(self.path.read_text()), {
            "Alice": {"enabled": True, "blacklist": [], "whitelist": []}
        })
        self.main.logger.error.assert_not_called()

    def test_invalid_json_and_encoding_preserved_after_join_and_ui_access(self):
        for original in (b'{"Bob": false,', b'\xff\xfe'):
            with self.subTest(original=original):
                self.sender.messages.clear()
                self.path.write_bytes(original)
                tpa = TPA(self.main)
                self.assert_unavailable(tpa, original)

    def test_invalid_schema_preserved_without_partial_legacy_migration(self):
        invalid_values = [
            [], None, 7,
            {"Alice": False, "Bob": "invalid"},
            {"Bob": {"enabled": "false"}},
            {"Bob": {"enabled": 1}},
            {"Bob": {"blacklist": "Alice"}},
            {"Bob": {"whitelist": None}},
            {"Bob": {"blacklist": ["Alice", 5]}},
            {"Bob": {"whitelist": [True]}},
        ]
        for value in invalid_values:
            with self.subTest(value=value):
                self.write_settings(value)
                original = self.path.read_bytes()
                tpa = TPA(self.main)
                self.assert_unavailable(tpa, original)

    def test_unreadable_file_is_never_overwritten(self):
        self.write_settings({"Bob": False})
        original = self.path.read_bytes()
        with patch("builtins.open", side_effect=PermissionError("permission denied")):
            tpa = TPA(self.main)
        self.assert_unavailable(tpa, original)

    def test_dangling_symlink_is_not_treated_as_missing_settings(self):
        self.path.symlink_to(Path(self.tempdir.name) / "missing-target.json")
        tpa = TPA(self.main)
        tpa.on_player_join(SimpleNamespace(player=self.sender))
        self.assertTrue(self.path.is_symlink())
        self.assertIsNone(tpa._TPA__tpa_setting_data)
        self.assertFalse(tpa._TPA__request_allowed("Alice", "Bob"))
        self.main.logger.error.assert_called_once()

    def test_legacy_boolean_migration_keeps_enabled_and_disabled_settings(self):
        self.write_settings({"Alice": True, "Bob": False})
        tpa = TPA(self.main)
        self.assertEqual(json.loads(self.path.read_text()), {
            "Alice": {"enabled": True, "blacklist": [], "whitelist": []},
            "Bob": {"enabled": False, "blacklist": [], "whitelist": []},
        })
        self.assertTrue(tpa._TPA__request_allowed("Bob", "Alice"))
        self.assertFalse(tpa._TPA__request_allowed("Alice", "Bob"))

    def test_blacklist_precedence_casefold_and_whitespace_are_preserved(self):
        self.write_settings({"Bob": {
            "enabled": True,
            "blacklist": [" aLiCe ", ""],
            "whitelist": ["ALICE", " Charlie ", " "],
        }})
        tpa = TPA(self.main)
        self.assertFalse(tpa._TPA__request_allowed("Alice", "Bob"))
        self.assertFalse(tpa._TPA__is_whitelisted("aLiCe", "Bob"))
        self.assertTrue(tpa._TPA__request_allowed("CHARLIE", "Bob"))
        self.assertTrue(tpa._TPA__is_whitelisted("charlie", "Bob"))
        self.assertEqual(json.loads(self.path.read_text())["Bob"], {
            "enabled": True, "blacklist": ["aLiCe"], "whitelist": ["Charlie"]
        })

    def test_missing_fields_keep_default_compatibility(self):
        self.write_settings({"Bob": {"blacklist": ["Alice"]}})
        tpa = TPA(self.main)
        self.assertFalse(tpa._TPA__request_allowed("Alice", "Bob"))
        self.assertTrue(tpa._TPA__request_allowed("Charlie", "Bob"))
        self.assertFalse(tpa._TPA__is_whitelisted("Charlie", "Bob"))

    def test_list_edits_move_names_between_lists_case_insensitively(self):
        self.write_settings({"Bob": {"blacklist": ["Alice"], "whitelist": []}})
        tpa = TPA(self.main)
        self.assertTrue(tpa._TPA__add_name_to_list(self.acceptor, "whitelist", "aLiCe"))
        self.assertEqual(json.loads(self.path.read_text())["Bob"], {
            "enabled": True, "blacklist": [], "whitelist": ["aLiCe"]
        })
        tpa._TPA__remove_list_entry("whitelist", "ALICE")(self.acceptor)
        self.assertFalse(tpa._TPA__is_whitelisted("Alice", "Bob"))

    def test_failed_migration_keeps_original_and_disables_requests(self):
        self.write_settings({"Bob": False})
        original = self.path.read_bytes()
        with patch("endstone_utp.storage.os.replace", side_effect=OSError("replace failed")):
            tpa = TPA(self.main)
        self.assert_unavailable(tpa, original)
        self.assertEqual(list(Path(self.tempdir.name).iterdir()), [self.path])

    def test_failed_initial_save_does_not_create_usable_defaults(self):
        with patch("endstone_utp.functions.tpa.atomic_write_json", side_effect=OSError("disk full")) as write:
            tpa = TPA(self.main)
            tpa.on_player_join(SimpleNamespace(player=self.sender))
            tpa.settings_main(self.sender)
            tpa.tpa_main(self.sender)
        write.assert_called_once()
        self.assertFalse(self.path.exists())
        self.assertIsNone(tpa._TPA__tpa_setting_data)
        self.assertEqual(self.sender.forms, [])
        self.main.logger.error.assert_called_once()

    def test_failed_save_preserves_file_and_blocks_stale_forms_and_operators(self):
        self.write_settings({"Bob": {"enabled": True, "blacklist": [], "whitelist": []}})
        original = self.path.read_bytes()
        self.sender.is_op = True
        tpa = TPA(self.main)
        tpa.tpa_main(self.sender)
        stale_request = self.sender.forms.pop()
        stale_accept = tpa._TPA__request_handler("Alice", self.sender.xuid, "TPA", "accept")
        with patch("endstone_utp.storage.os.replace", side_effect=OSError("disk full")):
            tpa._TPA__toggle_requests(self.acceptor)
        stale_request.on_submit(self.sender, "[0, 2]")
        stale_accept(self.acceptor)
        tpa._TPA__toggle_requests(self.acceptor)
        tpa._TPA__manage_list("blacklist")(self.acceptor)
        tpa._TPA__add_online_player("whitelist")(self.acceptor)
        tpa._TPA__add_offline_player("blacklist")(self.acceptor)
        tpa._TPA__add_list_entry("whitelist", "Alice")(self.acceptor)
        tpa._TPA__remove_list_entry("blacklist", "Alice")(self.acceptor)
        self.assertEqual(self.sender.teleports, [])
        self.assertEqual(self.acceptor.teleports, [])
        self.assertEqual(self.acceptor.forms, [])
        self.assert_unavailable(tpa, original)
        self.assertEqual(list(Path(self.tempdir.name).iterdir()), [self.path])

    def test_repaired_file_is_reloaded_only_after_reinitialization(self):
        self.path.write_text("broken", encoding="utf-8")
        tpa = TPA(self.main)
        self.write_settings({"Bob": False})
        tpa.on_player_join(SimpleNamespace(player=self.sender))
        self.assertIsNone(tpa._TPA__tpa_setting_data)
        self.assertEqual(json.loads(self.path.read_text()), {"Bob": False})
        restored = TPA(self.main)
        self.assertFalse(restored._TPA__request_allowed("Alice", "Bob"))
        self.assertIsNotNone(restored._TPA__tpa_setting_data)

    def test_unavailable_message_is_localized(self):
        self.path.write_text("broken", encoding="utf-8")
        tpa = TPA(self.main)
        self.sender.locale = "zh_CN"
        tpa.settings_main(self.sender)
        self.assertIn("不可用", self.sender.messages[-1])
        self.assertIn("重启", self.sender.messages[-1])


if __name__ == "__main__":
    unittest.main()
