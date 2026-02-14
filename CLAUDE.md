# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Stock Auditor — a modular Python tool that automates quarterly stock trading account audits on [ChinaClear](https://passport.chinaclear.cn). It uses Selenium to log in (with ddddocr-based CAPTCHA recognition), query Category A and B accounts, save screenshots, and optionally email results as zip attachments.

## Commands

```bash
# Run (requires config.yml with credentials via environment variables)
PYTHONPATH=src python -m stock_auditor

# Run with custom config
PYTHONPATH=src python -m stock_auditor --config path/to/config.yml

# Send emails only (skip audit, use existing screenshots)
PYTHONPATH=src python -m stock_auditor --email-only

# Run tests
PYTHONPATH=src pytest

# Run tests with coverage
PYTHONPATH=src pytest --cov=stock_auditor --cov-report=term-missing
```

## Dependencies

Defined in `pyproject.toml` and `requirements.txt`. Core: `selenium`, `webdriver-manager`, `ddddocr`, `pyyaml`. Dev: `pytest`, `pytest-cov`.

```bash
pip install -r requirements.txt
```

## Architecture

Modular package under `src/stock_auditor/`:

| Module | Responsibility |
|---|---|
| `config.py` | YAML config loading + environment variable merging |
| `quarter.py` | Pure date/quarter calculation logic |
| `browser.py` | Chrome browser lifecycle (headless support) |
| `captcha.py` | CAPTCHA screenshot + ddddocr OCR (in-memory, no disk I/O) |
| `login.py` | ChinaClear login flow with retry |
| `audit.py` | Audit query execution + screenshot capture |
| `email_sender.py` | SMTP email with zip attachment |
| `main.py` | Orchestrator + CLI entry point |

### Flow per user

1. Load config (YAML + env vars) → 2. Compute previous quarter dates → 3. Create output directory → 4. Launch browser → 5. Login (with CAPTCHA OCR, up to N retries) → 6. Execute audit queries + screenshots → 7. Close browser → 8. Send email report (if enabled)

## Configuration

- `config.example.yml` — template with all options (committed to repo)
- `config.yml` — real config with secrets (gitignored)
- Credentials injected via environment variables: `STOCK_USER_{i}_USERNAME`, `STOCK_USER_{i}_PASSWORD`, `SMTP_SENDER`, `SMTP_AUTH_CODE`
- `HEADLESS=true` enables headless Chrome (used in CI)

## CI/CD

- `.github/workflows/ci.yml` — runs tests on push/PR (Python 3.10-3.12 matrix)
- `.github/workflows/quarterly-audit.yml` — scheduled quarterly execution with `workflow_dispatch` manual trigger

## Key Implementation Details

- Date inputs have `readonly` attributes removed via `execute_script()` before filling
- CAPTCHA OCR uses in-memory byte stream (`screenshot_as_png`) — no temp files
- Output screenshots named `{category}-{index}.{market}.png` (e.g., `A-1.SH.png`)
- Output directory defaults to `./output/{user}-{quarter}/`
- Single user failure does not block other users from being audited
