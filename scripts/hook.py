#!/usr/bin/env python3
"""Hook entry point.

UserPromptSubmit -> remember the session cost at the start of the prompt.
Stop / SessionEnd -> write the final session report (if enabled).
"""
import json
import os
import sys

sys.path.insert(0, __import__("os").path.dirname(__file__))
import ctlib as ct  # noqa: E402


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return
    sid = data.get("session_id") or "unknown"
    event = data.get("hook_event_name") or ""
    proj = ct.project_dir_of(data)
    ct.sync_plugin_options()
    cfg = ct.load_config(proj)

    if event in ("SessionStart", "UserPromptSubmit"):
        selected = os.environ.get("CLAUDE_PLUGIN_OPTION_CONFIGURE_STATUS_LINE")
        if selected is not None:
            try:
                normalized = selected.strip().lower()
                if normalized not in ("true", "false"):
                    raise ValueError("expected true/false")
                enabled = normalized == "true"
                ct.sync_status_line(
                    enabled,
                    os.environ.get("CLAUDE_PLUGIN_ROOT")
                    or os.path.dirname(os.path.dirname(__file__)),
                    sys.executable,
                )
            except (OSError, ValueError, TypeError) as exc:
                print(f"Cost Tracker: could not configure the status line: {exc}",
                      file=sys.stderr)

    if event == "UserPromptSubmit":
        def upd(s):
            s["baseline"] = float(s.get("last_total", 0.0))
        ct.update_state(sid, upd)
    elif event in ("Stop", "SessionEnd") and cfg["create_session_report"]:
        tx = ct.update_usage(sid, data.get("transcript_path"))
        cost = float(ct.read_json(ct.state_path(sid)).get("last_total", 0.0))
        ct.write_report(cfg, sid, data.get("cwd") or proj, tx, cost, force=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # never break the user's session
