# claude-usage-tray — notes for Claude Code

Linux systray applet (StatusNotifierItem via AppIndicator, GTK 3) showing
claude.ai plan usage. User docs: README.md (EN) and README.fr.md (FR).

## Layout

```
claude_usage_tray/
├── main.py           RefreshWorker (daemon thread, backoff, fast retry) + main()
├── tray.py           UsageTray (AppIndicator menu), open_login_page()
├── api_client.py     ClaudeUsageClient, UsageSnapshot, UsageWindow;
│                     errors: ApiError > AuthError, BlockedError
├── cookie_reader.py  profiles.ini → cookies.sqlite → sessionKey
├── config.py         ~/.config/claude-usage-tray/config.toml
├── i18n.py           _(), set_language(), detect_language()
└── locales/fr.py     French catalog (English is the source language)
packaging/*.in        autostart / systemd templates, filled by install.sh
diag_usage.py         end-to-end diagnostic (cookie rows, Cloudflare, API)
tests/                unittest, no network, no GTK
```

## Rules

- **Threading:** `RefreshWorker` runs in a daemon thread. Every UI update
  goes through `GLib.idle_add(...)`, never directly from the worker.
- **i18n:** every user-facing string is English, wrapped in `_()` at use
  time (never at import time: the language is set in `main()` after the
  config is loaded). Use `str.format` placeholders, never f-strings inside
  `_()`. Add the French translation to `locales/fr.py`;
  `tests/test_i18n.py` fails on missing/stale entries or placeholder
  mismatches. Strings translated indirectly (like `tray.WEEKDAYS`) must be
  listed in `INDIRECT_TUPLES` in that test.
- **Error semantics:** `AuthError` / `CookieError` → `needs_login=True` (the
  "Sign in again" menu item). `BlockedError` (Cloudflare challenge) and other
  `ApiError` → `needs_login=False`; signing in again would not help.
- **HTTP headers:** the `Sec-Fetch-*` headers are what gets past Cloudflare;
  without them every request gets `403` + `cf-mitigated: challenge`,
  regardless of User-Agent. Do not remove them.
- **Firefox cookies:** `moz_cookies.expiry` is in milliseconds on recent
  Firefox (seconds on older ones) — use `expiry_seconds()`.
- **`/usage` schema:** per-model weekly limits are in `limits[]`
  (`kind == "weekly_scoped"`, `scope.model.display_name`). The legacy
  `seven_day_<model>` keys are still parsed as a fallback; they are `null`
  today. `seven_day_breakdown` is a per-surface split, not a model.

## Conventions

- **Tabs** for indentation, including Python.
- Code comments and docstrings in **English**.
- `from __future__ import annotations`, type hints everywhere,
  `@dataclass(frozen=True)` for data structures.
- No new dependency without a strong reason: `requests` + system `python3-gi`
  only; tests use stdlib `unittest`.

## Commands

```bash
./.venv/bin/python -m unittest discover -s tests -t .   # tests
./.venv/bin/python diag_usage.py                        # live diagnostic
./.venv/bin/python -m claude_usage_tray                 # run in foreground
pkill -f 'venv/bin/[p]ython -m claude_usage_tray'       # stop the running applet
dex ~/.config/autostart/claude-usage-tray.desktop       # start it again
```
