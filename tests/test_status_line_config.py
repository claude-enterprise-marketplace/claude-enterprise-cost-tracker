import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
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


class SessionSummaryTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.home = Path(self.temp_dir.name)
        self.home_patch = patch.object(ctlib, "HOME_DIR", self.home / ".claude" / "cost-tracker")
        self.home_patch.start()
        self.addCleanup(self.home_patch.stop)
        self.transcript = self.home / "session.jsonl"

    def append_entry(self, entry):
        with self.transcript.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(entry) + "\n")

    def test_report_includes_model_summary_in_both_formats(self):
        prompt = "We updated the plugin to generate a concise session summary."
        self.append_entry({"type": "user", "message": {"content": prompt}})
        self.append_entry({
            "type": "assistant",
            "message": {
                "id": "message-1",
                "model": "test-model",
                "usage": {
                    "input_tokens": 10,
                    "output_tokens": 5,
                    "cache_creation_input_tokens": 0,
                    "cache_read_input_tokens": 0,
                },
            },
        })

        tx = ctlib.update_usage("session-1", str(self.transcript))
        tx["summary"] = "Summarized plugin improvements and report generation."

        for report_format in ("markdown", "json"):
            cfg = dict(ctlib.DEFAULTS)
            cfg.update(
                create_session_report=True,
                report_dir=str(self.home / "reports"),
                report_format=report_format,
            )
            report_path = ctlib.write_report(
                cfg, f"session-{report_format}", str(self.home), tx, 0.25, force=True
            )
            self.assertIsNotNone(report_path)
            if report_format == "json":
                report = json.loads(Path(report_path).read_text(encoding="utf-8"))
                self.assertEqual(report["summary"], tx["summary"])
            else:
                report = Path(report_path).read_text(encoding="utf-8")
                self.assertIn(f"| Summary | {tx['summary']} |", report)

    def test_prompt_context_excludes_slash_commands(self):
        self.append_entry({"type": "user", "message": {"content": "Hi!"}})
        self.append_entry({
            "type": "user",
            "message": {"content": "<command-message>cost-tracker:config</command-message>"},
        })
        self.append_entry({"type": "user", "message": {"content": "Add a report summary please"}})

        prompts = ctlib.session_prompt_context(str(self.transcript))

        self.assertEqual(prompts, ["Hi!", "Add a report summary please"])

    def test_model_summary_is_capped_and_nested_hooks_are_disabled(self):
        prompt = " ".join(f"word{i}" for i in range(35))
        self.append_entry({"type": "user", "message": {"content": prompt}})
        output = " ".join(f"summary{i}" for i in range(35))
        with patch.object(ctlib.shutil, "which", return_value="/usr/bin/claude"), \
                patch.object(ctlib.subprocess, "run", return_value=SimpleNamespace(
                    returncode=0, stdout=output, stderr=""
                )) as run:
            with patch.dict("os.environ", {"CLAUDECODE": "1"}):
                summary = ctlib.generate_session_summary(str(self.transcript))

        self.assertEqual(summary, " ".join(f"summary{i}" for i in range(30)))
        args = run.call_args.args[0]
        self.assertIn("--no-session-persistence", args)
        self.assertIn("--disable-slash-commands", args)
        self.assertIn('{"disableAllHooks":true}', args)
        self.assertNotIn("CLAUDECODE", run.call_args.kwargs["env"])
        self.assertIn(json.dumps([prompt]), run.call_args.kwargs["input"])

    def test_summary_generation_requires_transcript_prompts(self):
        with patch.object(ctlib.shutil, "which") as which:
            self.assertEqual(ctlib.generate_session_summary(str(self.transcript)), "")
        which.assert_not_called()


if __name__ == "__main__":
    unittest.main()
