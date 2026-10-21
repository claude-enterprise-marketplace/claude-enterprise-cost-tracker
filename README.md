# cost-tracker (Claude Code plugin)

Status line, shown below the prompt:

    prompt $0.0412 · 3.2k tok  │  session $0.0912 · 12.4k tok

Optional per-session report (date, repository, branch, requests sent to Claude, total cost, total tokens).

## Install
Local test:  `claude --plugin-dir ./cost-tracker`
Enterprise:  host in a git repo with `.claude-plugin/marketplace.json`, then
`/plugin marketplace add tcorral` and `/plugin install cost-tracker@tcorral`.
Windows: replace `python3` with `python` in `settings.json` and `hooks/hooks.json`.

## Configuration
Change with `/cost-tracker:config` or edit the JSON files directly.

    /cost-tracker:config                         show effective settings
    /cost-tracker:config keys                    list all settings
    /cost-tracker:config set show_cost_session false
    /cost-tracker:config set create_session_report true --project
    /cost-tracker:config reset [key] [--project]

| Setting | Default | Meaning |
|---|---|---|
| show_cost_last_prompt | true | cost (USD) of the last prompt |
| show_cost_session | true | accumulated session cost |
| show_tokens_last_prompt | true | tokens of the last prompt |
| show_tokens_session | true | accumulated session tokens |
| create_session_report | false | create/update the report document |
| include_cache_tokens | false | count cache creation/read tokens in totals |
| token_format | compact | `compact` (12.3k) or `full` (12,345) |
| cost_decimals | 4 | decimals for dollar amounts |
| separator / group_separator | ` · ` / `  │  ` | status line separators |
| report_dir | ~/.claude/session-reports | report folder (relative = project) |
| report_format | markdown | `markdown` or `json` |

Priority (low to high): defaults < `~/.claude/cost-tracker/config.json` < `<project>/.claude/cost-tracker.json` < env var `CLAUDE_COST_TRACKER_<KEY>` (e.g. `CLAUDE_COST_TRACKER_CREATE_SESSION_REPORT=true`; admins can set these through the `env` block of managed settings).

## How numbers are computed
- Cost: `cost.total_cost_usd` from Claude Code (client-side estimate). Last prompt = current total minus the total at the moment the prompt was submitted (UserPromptSubmit hook).
- Tokens and request count: read from the session transcript (one request = one API response, deduplicated). Last prompt = everything after your most recent prompt.
- Report: one file per session, updated in place on every status refresh and on Stop/SessionEnd.

## Known limits
- If the user already has their own `statusLine` in settings, it wins over the plugin's. The report cost then stays at 0/n.a. because only the status line receives cost data.
- Subagent usage is included only if Claude Code writes it to the main transcript.
