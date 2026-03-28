# DONE

Completion timestamp: 2026-03-28T20:46:29+00:00
Standalone repo: https://github.com/srijan-at-qwertystars/sycophancy-smoke-test

Summary of what was built:
- A Python CLI and library for parsing simple transcript files and scoring sycophancy-related signals.
- Heuristics for affirmation bias, weak pushback, unsupported certainty, and missing evidence-seeking.
- JSON/text reports plus good/bad transcript fixtures and passing automated tests.

Quality self-score: 8/10

Lessons learned:
- Lightweight transcript formats make offline evaluation tools easy to author and test.
- Heuristic scoring is enough for a useful smoke test even without ML models or APIs.
- Comparison output turns a subjective concern into something teams can regression-test locally.
