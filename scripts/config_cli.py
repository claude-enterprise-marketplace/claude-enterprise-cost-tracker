#!/usr/bin/env python3
"""Show or change cost-tracker settings.

  config_cli.py [show]
  config_cli.py keys
  config_cli.py get <key>
  config_cli.py set <key> <value> [--project]
  config_cli.py reset [<key>] [--project]
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import ctlib as ct  # noqa: E402


def target(args):
    if "--project" in args:
        args.remove("--project")
        return ct.project_config_path(os.getcwd()), "project"
    return ct.USER_CONFIG, "user"


def show():
    cfg, src = ct.load_config_with_sources(os.getcwd())
    w = max(len(k) for k in cfg)
    print(f"{'setting'.ljust(w)}  value                       source")
    for k, v in cfg.items():
        print(f"{k.ljust(w)}  {json.dumps(v):<26} {src[k]}")
    print("\nPriority: default < user (~/.claude/cost-tracker/config.json) "
          "< project (.claude/cost-tracker.json) < env (CLAUDE_COST_TRACKER_<KEY>)")


def main(argv):
    cmd = argv[0] if argv else "show"
    rest = argv[1:]
    if cmd == "show":
        show()
    elif cmd == "keys":
        for k, (d, desc) in ct.SETTINGS.items():
            print(f"{k:<24} default={d!r:<28} {desc}")
    elif cmd == "get" and len(rest) == 1 and rest[0] in ct.DEFAULTS:
        print(ct.load_config(os.getcwd())[rest[0]])
    elif cmd == "set":
        path, scope = target(rest)
        if len(rest) < 2 or rest[0] not in ct.DEFAULTS:
            sys.exit("usage: set <key> <value> [--project]   (see: keys)")
        key, value = rest[0], " ".join(rest[1:])
        try:
            value = ct.coerce(value, key)
        except (ValueError, TypeError) as e:
            sys.exit(f"error: {e}")
        conf = ct.read_json(path)
        conf[key] = value
        ct.write_json(path, conf)
        print(f"{key} = {value!r}  ({scope}: {path})")
    elif cmd == "reset":
        path, scope = target(rest)
        conf = ct.read_json(path)
        if rest:
            conf.pop(rest[0], None)
        else:
            conf = {}
        ct.write_json(path, conf)
        print(f"reset done ({scope}: {path})")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
