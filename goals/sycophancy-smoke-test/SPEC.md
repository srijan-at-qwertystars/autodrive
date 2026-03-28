# Sycophancy Smoke Test

**One-liner**: CLI and library that scores chat transcripts for over-agreement, missing pushback, and confidence-without-evidence patterns.
**Started**: 2026-03-28T20:22:16Z
**Max cycles**: 3
**Cycle**: 1 of 3
**Status**: IN_PROGRESS

## Deliverables
- [ ] A Python CLI and library for parsing transcript files and scoring sycophancy-related signals
- [ ] Heuristics for affirmation bias, weak disagreement, unsupported certainty, and lack of evidence-seeking behavior
- [ ] A machine-readable JSON report plus a readable terminal summary
- [ ] Good and bad conversation fixtures that demonstrate materially different scores
- [ ] An automated test suite and local README with usage examples

## Success Criteria (machine-verifiable)
- `python3 sycophancy_smoke_test.py --help` exits successfully inside this goal directory
- `python3 sycophancy_smoke_test.py score fixtures/bad-chat.txt --format json` produces valid JSON with at least one flagged turn
- `python3 sycophancy_smoke_test.py compare fixtures/good-chat.txt fixtures/bad-chat.txt --format json` shows a higher overall sycophancy score for the bad transcript than the good transcript
- `README.md` exists in the goal directory and includes installation and usage instructions
- The goal directory includes an automated test suite that passes with the existing project test command

## Sub-Agent Plan
- Agent 1: Build the transcript parser, scoring engine, CLI commands, and JSON/text rendering
- Agent 2: Add fixtures, tests, README docs, and comparison output polishing

## Notes
The selected idea tied for the highest discovery score and won on local-first execution risk.
This goal should stay fully offline and heuristic-driven so teams can run it on transcripts without model calls or external services.
