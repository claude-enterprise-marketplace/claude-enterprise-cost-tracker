---
description: Show or change Cost Tracker settings (status line, reports, summaries)
argument-hint: [show | keys | get <key> | set <key> <value> [--project] | reset [key] [--project]]
allowed-tools: Bash(python3:*)
---

Run the Cost Tracker configuration tool with the Bash tool and show its output as-is, without extra commentary:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/config_cli.py" $ARGUMENTS
```

If `${CLAUDE_PLUGIN_ROOT}` is empty, the plugin folder path is stored in `~/.claude/cost-tracker/plugin_root`; use `$(cat ~/.claude/cost-tracker/plugin_root)/config_cli.py` instead.
With no arguments the tool prints the current settings.
