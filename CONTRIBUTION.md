# Contributing

Thanks for your interest in improving the Claude Code cost-tracker plugin.

## Before you start

- For bugs, include the steps to reproduce, expected and actual behavior, and relevant Claude Code or Python versions.
- For feature proposals, describe the use case and how the change should behave.
- Never include session transcripts, credentials, or other private data in an issue or pull request. Redact examples and logs.

## Making changes

1. Fork the repository and create a branch for your change.
2. Keep changes focused and preserve existing configuration defaults and behavior unless the change explicitly intends otherwise.
3. Update the README when user-facing behavior, installation, or configuration changes.
4. Review the diff before opening a pull request. Explain what changed, why, and how you verified it.

The main implementation is in `scripts/`; `hooks/hooks.json` registers the hooks, `settings.json` provides plugin settings, and `commands/` contains the configuration command documentation. Avoid adding dependencies unless they are necessary and document any new setup requirements.

## Validation

Run checks appropriate to your change:

- Run the automated tests with `python3 -m unittest discover -s tests -v`.
- For Python changes, run `python3 -m py_compile scripts/*.py tests/*.py`.
- For changes to JSON files, validate each changed file with `python3 -m json.tool <file>`.
- For plugin behavior, follow the local test instructions in the README and try the affected feature in Claude Code.
- For configuration changes, check both the default and override behavior, including project and environment settings where applicable.

Include the checks you ran and any manual testing limitations in your pull request.
