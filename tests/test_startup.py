import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.stubs import Logger, Player, install

install()
from endstone_utp.config import DEFAULT_CONFIG
from endstone_utp.main import Main


class StartupTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.data = self.root / "plugins" / "utp"
        self.data.mkdir(parents=True)
        patcher = patch("endstone_utp.main.os.getcwd", return_value=str(self.root))
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_constructor_does_not_access_files_or_uninitialized_logger(self):
        main = Main()
        self.assertEqual(list(self.data.iterdir()), [])
        self.assertFalse(hasattr(main, "config_funct"))
        main.logger = Logger()
        main.on_load()
        self.assertEqual(main.config_funct.config_data, DEFAULT_CONFIG)
        self.assertTrue((self.data / "tpa_setting.json").exists())
        self.assertEqual(main.logger.errors, [])

    def test_bad_config_fails_load_with_logger_ready_and_preserves_file(self):
        path = self.data / "config.json"
        path.write_text("broken config")
        main = Main()
        main.logger = Logger()
        with self.assertRaises(ValueError):
            main.on_load()
        self.assertEqual(path.read_text(), "broken config")
        self.assertIn("file left unchanged", main.logger.errors[-1])

    def test_bad_tpa_keeps_other_functions_loaded_and_reports_unavailable(self):
        path = self.data / "tpa_setting.json"
        path.write_text("broken settings")
        main = Main()
        main.logger = Logger()
        main.on_load()
        self.assertEqual(main.config_funct.config_data, DEFAULT_CONFIG)
        self.assertTrue(hasattr(main, "home_funct"))
        player = Player()
        main.tpa_funct.settings_main(player)
        self.assertIn("unavailable", player.messages[-1])
        self.assertEqual(path.read_text(), "broken settings")
        self.assertIn("TPA requests and settings are disabled", main.logger.errors[-1])


if __name__ == "__main__":
    unittest.main()
