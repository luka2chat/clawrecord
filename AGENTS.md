# AGENTS.md

## Cursor Cloud specific instructions

### Overview

ClawRecord is a static-site-generation pipeline that turns OpenClaw usage data into a gamified dashboard. There are no external dependencies — all Python scripts use stdlib only, and the Node.js hook uses only built-in modules.

### Running the pipeline

The full pipeline is: `collect.py` -> `score.py` -> `generate_pages.py`. See `README.md` for details.

- `python3 scripts/collect.py` — Reads OpenClaw data from `~/.openclaw/`. Without OpenClaw installed, it produces empty metrics. The repo ships with pre-existing data in `data/raw/metrics.json` which can be used directly.
- `python3 scripts/score.py` — Computes XP, levels, achievements, skills from metrics. Outputs to `data/`.
- `python3 scripts/generate_pages.py` — Generates `docs/index.html`, `docs/index_zh.html`, and `docs/styles.css`.

### Serving the dashboard locally

```bash
cd docs && python3 -m http.server 8080
```

Then open `http://localhost:8080/index.html`.

### Gotchas

- All Python scripts emit `DeprecationWarning` about `datetime.utcnow()` on Python 3.12+. This is cosmetic and does not affect functionality.
- `collect.py` will overwrite `data/raw/metrics.json` with empty data if OpenClaw is not installed. To preserve demo data for testing, either skip `collect.py` or restore from git afterward (`git checkout -- data/raw/metrics.json`).
- The Node.js hook (`hooks/clawrecord-hook/handler.js`) uses ES module syntax; validate with `node -e "import('./hooks/clawrecord-hook/handler.js')"`.

### Linting / Testing

No formal test suite or linter configuration exists in this repository. Validation is done by running the pipeline end-to-end and verifying the generated HTML output.
