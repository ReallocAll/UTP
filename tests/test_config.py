import json
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from tests.stubs import Player, install, make_main

install()
from endstone_utp.config import ADMIN_PERMISSION, Config, DEFAULT_CONFIG, GLOBAL_FIELDS, TOGGLE_FIELDS, validate_config
from endstone_utp.lang import CONFIG_TEXT, Lang
from endstone_utp.main import Main
from endstone_utp.storage import FileChangedError, atomic_write_json


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "config.json"
        self.main = make_main(self.directory.name)
        self.config = Config(self.main)
        self.main.config_funct = self.config
        self.player = Player(admin=True)

    def editor(self, index=2):
        self.config.reload_config_main(self.player)
        self.player.forms[-1].buttons[index].on_click(self.player)
        return self.player.forms[-1]

    def submit(self, form, values):
        form.on_submit(self.player, json.dumps(values))

    def test_defaults_and_admin_permission_contract(self):
        self.assertEqual(json.loads(self.path.read_text()), DEFAULT_CONFIG)
        self.assertEqual(Main.permissions[ADMIN_PERMISSION]["default"], "op")
        self.assertIs(Main.permissions["Main.command.utp"]["default"], True)
        for admin in (False, True):
            with self.subTest(admin=admin):
                main = object.__new__(Main)
                main.lang_funct = self.main.lang_funct
                main.config_funct = SimpleNamespace(
                    config_data={"is_enabled": dict.fromkeys(TOGGLE_FIELDS, False)},
                    reload_config_main=self.config.reload_config_main,
                )
                main.server = SimpleNamespace(plugin_manager=SimpleNamespace(get_plugin=lambda name: None))
                main.admin_teleport_funct = SimpleNamespace(
                    button_text=lambda player: "Admin teleport", admin_teleport_main=lambda player: None
                )
                player = Player(admin=admin)
                # An explicit permission deny must win even for an operator.
                player.is_op = True
                main.on_command(player, SimpleNamespace(name="utp"), [])
                callbacks = [button.on_click for button in player.forms[-1].buttons]
                self.assertEqual(self.config.reload_config_main in callbacks, admin)

    def test_permission_rechecked_at_menu_entry_reload_and_submit(self):
        self.config.reload_config_main(self.player)
        menu = self.player.forms[-1]
        form = self.editor()
        toggle_form = self.editor(1)
        before = self.path.read_bytes()
        self.player.admin = False
        self.player.is_op = True
        count = len(self.player.forms)
        self.config.reload_config_main(self.player)
        for button in menu.buttons:
            button.on_click(self.player)
        self.submit(form, ["6", "30", "0.1", "2000", "60"])
        self.submit(toggle_form, [False] * len(TOGGLE_FIELDS))
        self.assertEqual(len(self.player.forms), count)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertTrue(all(m == "config.message.no_permission" for m in self.player.messages))

    def test_named_fields_independent_of_json_order_and_unknown_keys_preserved(self):
        candidate = dict(reversed(list(deepcopy(DEFAULT_CONFIG).items())))
        candidate["is_enabled"] = dict(reversed(list(candidate["is_enabled"].items())))
        candidate["custom_extension"] = {"value": 42}
        self.path.write_text(json.dumps(candidate))
        self.config.reload_from_disk(self.player)
        form = self.editor()
        self.assertEqual([control.label for control in form.controls], [f"config.field.{key}" for key, _ in GLOBAL_FIELDS])
        self.assertEqual([control.default_value for control in form.controls], ["5", "30", "0.01", "2000", "60"])
        self.submit(form, ["6", "31", "0.2", "2001", "61"])
        self.assertEqual([self.config.config_data[key] for key, _ in GLOBAL_FIELDS], [6, 31, 0.2, 2001, 61])
        form = self.editor(1)
        self.submit(form, [False, True, False, True, False, True])
        self.assertEqual([self.config.config_data["is_enabled"][key] for key in TOGGLE_FIELDS], [False, True, False, True, False, True])
        self.assertEqual(json.loads(self.path.read_text())["custom_extension"], {"value": 42})

    def test_invalid_modal_values_never_partially_update_disk_or_runtime(self):
        before = self.path.read_bytes()
        invalid = [None, {}, [], ["5"], ["5", "5", "5", "5", "5"],
                   ["5", "30", "nan", "2000", "60"], ["5", "30", "inf", "2000", "60"],
                   ["5", "30", "0.1", "0", "60"], ["5.0", "30", "0.1", "2000", "60"],
                   [5, "30", "0.1", "2000", "60"], ["5", "30", "0.1", "2000", "60", "extra"]]
        form = self.editor()
        for values in invalid:
            with self.subTest(values=values):
                self.submit(form, values)
                self.assertEqual(self.config.config_data, DEFAULT_CONFIG)
                self.assertEqual(self.path.read_bytes(), before)
        form.on_submit(self.player, "[")
        self.assertEqual(self.player.messages[-1], "message.error")
        form = self.editor(1)
        for values in ([True], [True] * 7, [1] * 6, {"home": True}, None):
            self.submit(form, values)
            self.assertEqual(self.config.config_data, DEFAULT_CONFIG)
            self.assertEqual(self.path.read_bytes(), before)

    def test_schema_rejects_wrong_types_missing_fields_and_nonfinite_rates(self):
        for key, _ in GLOBAL_FIELDS:
            invalid = [None, True, "5", 0, -1]
            invalid += [float("nan"), float("inf"), 1] if key == "death_penalty_rate" else [1.5]
            for value in invalid:
                with self.subTest(key=key, value=value):
                    candidate = deepcopy(DEFAULT_CONFIG)
                    candidate[key] = value
                    with self.assertRaises(ValueError):
                        validate_config(candidate)
        for candidate in ([], {}, {**DEFAULT_CONFIG, "is_enabled": []},
                          {**DEFAULT_CONFIG, "is_enabled": {**DEFAULT_CONFIG["is_enabled"], "home": 1}}):
            with self.assertRaises(ValueError):
                validate_config(candidate)

    def test_reload_reads_disk_and_preserves_good_snapshot_after_invalid_reload(self):
        candidate = deepcopy(DEFAULT_CONFIG)
        candidate["max_home"] = 2
        self.path.write_text(json.dumps(candidate))
        content = self.path.read_bytes()
        self.config.reload_from_disk(self.player)
        self.assertEqual(self.config.config_data, candidate)
        self.assertEqual(self.path.read_bytes(), content)
        good = self.config.config_data
        for bad in (b"{ broken", b"\xff", b"[]", b'{"max_home": NaN}'):
            self.path.write_bytes(bad)
            self.config.reload_from_disk(self.player)
            self.assertIs(self.config.config_data, good)
            self.assertEqual(self.path.read_bytes(), bad)
            self.assertEqual(self.player.messages[-1], "config.message.reload_failed")
        self.path.unlink()
        self.config.reload_from_disk(self.player)
        self.assertIs(self.config.config_data, good)
        self.assertFalse(self.path.exists())
        self.assertTrue(self.main.logger.errors)

    def test_invalid_startup_never_overwrites_the_original(self):
        for bad in (b"not json", b"\xff", b"[]"):
            self.path.write_bytes(bad)
            with self.assertRaises(ValueError):
                Config(self.main)
            self.assertEqual(self.path.read_bytes(), bad)

    def test_disk_edits_and_stale_open_forms_are_rejected(self):
        form = self.editor()
        edited = deepcopy(DEFAULT_CONFIG)
        edited["tpr_range"] = 800
        self.path.write_text(json.dumps(edited))
        edited_bytes = self.path.read_bytes()
        self.submit(form, ["6", "30", "0.1", "2000", "60"])
        self.assertEqual(self.path.read_bytes(), edited_bytes)
        self.assertEqual(self.config.config_data, DEFAULT_CONFIG)
        self.config.reload_from_disk(self.player)
        self.submit(form, ["6", "30", "0.1", "2000", "60"])
        self.assertEqual(self.config.config_data, edited)
        first = self.editor()
        stale = self.editor(1)
        self.submit(first, ["6", "30", "0.1", "800", "60"])
        saved_bytes = self.path.read_bytes()
        self.submit(stale, [False] * 6)
        self.assertEqual(self.path.read_bytes(), saved_bytes)
        self.assertEqual(self.player.messages[-1], "config.message.conflict")

    def test_failed_replace_leaves_active_and_persisted_config_unchanged(self):
        before = self.path.read_bytes()
        good = self.config.config_data
        form = self.editor()
        with patch("endstone_utp.storage.os.replace", side_effect=OSError("disk unavailable")):
            self.submit(form, ["6", "30", "0.1", "2000", "60"])
        self.assertEqual(self.path.read_bytes(), before)
        self.assertIs(self.config.config_data, good)
        self.assertEqual(self.player.messages[-1], "config.message.save_failed")
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    def test_snapshot_check_is_immediately_before_replace(self):
        before = self.path.read_bytes()
        def external_edit(_):
            self.path.write_text("external edit")
        with patch("endstone_utp.storage.os.fsync", side_effect=external_edit):
            with self.assertRaises(FileChangedError):
                atomic_write_json(self.path, DEFAULT_CONFIG, expected_content=before)
        self.assertEqual(self.path.read_text(), "external edit")
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    def test_new_localizations_work_with_existing_custom_language_files(self):
        directory = self.path.parent / "lang"
        directory.mkdir()
        custom = {"config.title": "My settings", "message.error": "Custom error"}
        for locale in ("zh_CN", "en_US"):
            (directory / f"{locale}.json").write_text(json.dumps(custom))
        lang = Lang(self.main)
        for locale in ("zh_CN", "en_US", "fr_FR"):
            self.player.locale = locale
            self.assertEqual(lang.get_text(self.player, "config.title"), "My settings")
            for key in CONFIG_TEXT["en_US"]:
                self.assertNotEqual(lang.get_text(self.player, key), key)
        self.assertEqual(json.loads((directory / "en_US.json").read_text()), custom)
        self.assertEqual(set(CONFIG_TEXT["zh_CN"]), set(CONFIG_TEXT["en_US"]))


if __name__ == "__main__":
    unittest.main()
