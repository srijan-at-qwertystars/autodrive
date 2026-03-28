# README Reality Check

**One-liner**: A CLI that compares a repo's setup docs against its actual scripts, files, and runnable commands to catch stale onboarding instructions.
**Started**: 2026-03-28T20:22:16Z
**Max cycles**: 3
**Cycle**: 1 of 3
**Status**: COMPLETE

## Deliverables
- [x] A Python CLI that audits README/setup instructions against a local repository
- [x] Rule coverage for common onboarding surfaces such as `package.json`, `Makefile`, Docker, and devcontainer files
- [x] JSON output describing missing files, missing scripts, and mismatched commands
- [x] An HTML report generated from the JSON findings
- [x] A sample repository fixture plus a documented demo run

## Success Criteria (machine-verifiable)
- `python3 readme_reality_check.py --help` exits successfully inside this goal directory
- `python3 readme_reality_check.py audit fixtures/demo-repo --format json` produces valid JSON with at least one finding
- `python3 readme_reality_check.py audit fixtures/demo-repo --format html --output out/demo-report.html` writes an HTML report file
- `README.md` exists in the goal directory and includes installation and usage instructions
- The goal directory includes an automated test suite that passes with the existing project test command

## Sub-Agent Plan
- Agent 1: Build the core CLI, README parser, repository scanners, and finding generation logic
- Agent 2: Add tests, a sample fixture repository, HTML reporting, and end-user documentation

## Notes
Discovery signals clustered around stale onboarding docs and setup friction in fast-moving repositories, especially agent-heavy projects.
The highest-scoring version of this idea is intentionally local-first: no API keys, no remote repo dependency, and outputs that are easy to verify in CI or from the terminal.
