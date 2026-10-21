import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import ctlib


class SyncStatusLineTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.base = Path(self.temp_dir.name)
        self.home = self.base / "home"
        self.home.mkdir()
        self.plugin_root = self.base / "plugin"
        (self.plugin_root / "scripts").mkdir(parents=True)
        (self.plugin_root / "scripts" / "statusline.py").write_text(
            "print('cost tracker')", encoding="utf-8"
        )
        self.settings_path = self.home / ".claude" / "settings.json"
        self.state_path = self.home / ".claude" / "cost-tracker" / "statusline-state.json"
        self.home_patch = patch.object(Path, "home", return_value=self.home)
        self.home_patch.start()
        self.addCleanup(self.home_patch.stop)
        self.state_patch = patch.object(ctlib, "STATUS_LINE_STATE", self.state_path)
        self.state_patch.start()
        self.addCleanup(self.state_patch.stop)

    def read_settings(self):
        return json.loads(self.settings_path.read_text(encoding="utf-8"))

    def write_settings(self, settings):
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        self.settings_path.write_text(json.dumps(settings), encoding="utf-8")

    def configure(self, enabled):
        ctlib.sync_status_line(enabled, self.plugin_root, "/usr/bin/python3")

    def test_enabling_replaces_and_saves_existing_status_line(self):
        original = {"type": "command", "command": "my-status-line"}
        self.write_settings({"theme": "dark", "statusLine": original})

        self.configure(True)

        settings = self.read_settings()
        self.assertEqual(settings["theme"], "dark")
        self.assertEqual(
            settings["statusLine"]["command"],
            f"/usr/bin/python3 {self.plugin_root.resolve()}/scripts/statusline.py",
        )
        self.configure(False)
        self.assertEqual(self.read_settings(), {"theme": "dark", "statusLine": original})
        self.assertFalse(self.state_path.exists())

    def test_disabling_removes_status_line_when_there_was_no_previous_one(self):
        self.write_settings({"theme": "dark"})

        self.configure(True)
        self.configure(False)

        self.assertEqual(self.read_settings(), {"theme": "dark"})

    def test_does_not_overwrite_user_edit_after_setup(self):
        self.write_settings({"statusLine": {"type": "command", "command": "original"}})
        self.configure(True)
        self.write_settings({"statusLine": {"type": "command", "command": "user edit"}})

        self.configure(True)
        self.assertEqual(
            self.read_settings()["statusLine"]["command"], "user edit"
        )
        self.assertFalse(self.state_path.exists())


if __name__ == "__main__":
    unittest.main()
