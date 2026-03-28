# README Reality Check

`readme_reality_check.py` audits local onboarding and setup documentation against what a repository actually contains.

## What it checks

- missing package scripts referenced by `npm`, `pnpm`, `bun`, or `yarn`
- missing `make` targets
- missing files or directories mentioned in setup commands
- Docker and devcontainer references that do not match repository contents

## Requirements

- Python 3.10+ (tested with the system `python3`)
- No third-party dependencies

## Installation

From this goal directory:

```bash
python3 --version
python3 readme_reality_check.py --help
```

## Usage

Audit a repository and print findings as text:

```bash
python3 readme_reality_check.py audit fixtures/demo-repo
```

Emit JSON:

```bash
python3 readme_reality_check.py audit fixtures/demo-repo --format json
```

Write an HTML report:

```bash
python3 readme_reality_check.py audit fixtures/demo-repo --format html --output out/demo-report.html
```

Run the automated tests:

```bash
python3 -m unittest discover -s tests -v
```

## Demo fixture

`fixtures/demo-repo/` is intentionally inconsistent. Its README references:

- `npm run dev`, but `package.json` does not define `dev`
- `python3 scripts/bootstrap.py`, but the file is missing
- `make setup`, but the `Makefile` only defines `serve`
- `docker compose up`, but no compose file exists
- `cp .env.sample .env`, but `.env.sample` is missing
