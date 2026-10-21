#!/usr/bin/env python3
"""Status line: cost and tokens for the last prompt and the session."""
import json
import sys
from datetime import datetime

sys.path.insert(0, __import__("os").path.dirname(__file__))
import ctlib as ct  # noqa: E402


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}
    sid = data.get("session_id") or "unknown"
    proj = ct.project_dir_of(data)
    cfg = ct.load_config(proj)
    total = float((data.get("cost") or {}).get("total_cost_usd") or 0.0)

    def upd(s):
        s["last_total"] = total
        s.setdefault("started", datetime.now().astimezone().isoformat(timespec="seconds"))
        if total < float(s.get("baseline", 0.0)):  # session cost reset (/clear)
            s["baseline"] = 0.0

    state = ct.update_state(sid, upd)
    last_cost = max(total - float(state.get("baseline", 0.0)), 0.0)

    need_tx = cfg["show_tokens_last_prompt"] or cfg["show_tokens_session"] or cfg["create_session_report"]
    tx = ct.update_usage(sid, data.get("transcript_path")) if need_tx else {"msgs": {}, "prompts": 0}
    totals = ct.usage_totals(tx)

    if cfg["create_session_report"]:
        try:
            ct.write_report(cfg, sid, proj, tx, total)
        except Exception:
            pass
    ct.remember_plugin_root()
    print(ct.render_status(cfg, last_cost, total, totals))


if __name__ == "__main__":
    main()
