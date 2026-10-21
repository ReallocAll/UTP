import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from tests.stubs import Player, install, make_main

install()
from endstone_utp.functions.home import Home


class HomeLimitTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.main = make_main(self.directory.name)
        self.main.config_funct = SimpleNamespace(config_data={"max_home": 1})
        self.home = Home(self.main)
        self.player = Player()
        self.home._Home__on_player_join(SimpleNamespace(player=self.player))
        self.path = Path(self.directory.name) / "home.json"

    def test_at_or_above_limit_blocks_opening(self):
        for count in (1, 2):
            self.home._Home__home_data[self.player.name] = {str(i): {} for i in range(count)}
            self.home._Home__add_home(self.player)
            self.assertEqual(self.player.forms, [])
            self.assertIn("add_home.message.fail.reason1", self.player.messages[-1])

    def test_second_open_form_cannot_exceed_limit(self):
        self.home._Home__add_home(self.player)
        first = self.player.forms[-1]
        self.home._Home__add_home(self.player)
        second = self.player.forms[-1]
        first.on_submit(self.player, '["first"]')
        second.on_submit(self.player, '["second"]')
        self.assertEqual(list(json.loads(self.path.read_text())[self.player.name]), ["first"])

    def test_limit_reduction_is_rechecked_on_submit(self):
        self.main.config_funct.config_data["max_home"] = 3
        self.home._Home__home_data[self.player.name] = {"existing": {}}
        self.home._Home__add_home(self.player)
        form = self.player.forms[-1]
        self.main.config_funct.config_data = {"max_home": 1}
        before = self.path.read_bytes()
        form.on_submit(self.player, '["new"]')
        self.assertEqual(list(self.home._Home__home_data[self.player.name]), ["existing"])
        self.assertEqual(self.path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
