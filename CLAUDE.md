# claude-usage-tray — notes for Claude Code

Linux systray applet (StatusNotifierItem via AppIndicator, GTK 3) showing
claude.ai plan usage. User docs: README.md (EN) and README.fr.md (FR).

## Layout

```
claude_usage_tray/
├── main.py           RefreshWorker (daemon thread, backoff, fast retry) + main()
├── tray.py           UsageTray (AppIndicator menu), open_login_page()
├── severity.py       icon policy: thresholds + pace alert (no GTK, tested)
├── icons.py          gauge icon as SVG (no GTK, tested), written by tray.py
│                     to $XDG_RUNTIME_DIR/claude-usage-tray/icons
├── formatting.py     percent, pace, text progress bars, remaining time,
│                     reset labels (no GTK)
├── notifications.py  UsageWatcher (what to notify, tested) + DesktopNotifier
│                     (org.freedesktop.Notifications over D-Bus)
├── system_events.py  refresh on resume (logind) and network up (Gio)
├── api_client.py     ClaudeUsageClient, UsageSnapshot, UsageWindow;
│                     errors: ApiError > AuthError, BlockedError, NetworkError
├── cookie_reader.py  Firefox roots (deb/XDG/snap/Flatpak) → profiles.ini
│                     → cookies.sqlite → sessionKey
├── config.py         ~/.config/claude-usage-tray/config.toml
├── i18n.py           _(), set_language(), detect_language()
└── locales/*.py      fr, de, es, it, nl, pt catalogs (English is the source language)
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
  `_()`. Add the translation to every `locales/*.py` catalog;
  `tests/test_i18n.py` fails on missing/stale entries or placeholder
  mismatches. Strings translated indirectly (like `formatting.WEEKDAYS`) must be
  listed in `INDIRECT_TUPLES` in that test.
- **Error semantics:** `AuthError` / `CookieError` → `needs_login=True` (the
  "Sign in again" menu item). `BlockedError` (Cloudflare challenge) and other
  `ApiError` → `needs_login=False`; signing in again would not help.
  `NetworkError` does not count towards the backoff (the server is not to
  blame; `SystemEventWatcher` refreshes when the network returns).
- **Menu:** dbusmenu carries only text and icons, so progress bars are text
  made of Unicode Block Elements (same advance width in UI fonts; avoid box
  drawing characters, which are narrower). Never make items insensitive:
  GNOME greys them out and they become hard to read.
- **Icon:** a generated gauge: ring = 5-hour usage, colour =
  `severity.snapshot_severity()` (worst of all windows), tick = elapsed share
  of the 5-hour window. Keep thresholds in `severity.py`, not in the UI.
  Each rendered state has its own icon name (`gauge_icon_name()`), because
  the panel caches icons by name; only the current SVG is kept on disk.
- **Notifications:** decided by `UsageWatcher.update()` from successive
  snapshots. The first snapshot is a baseline (no notice on restart); a
  reset is detected once the old `resets_at` has passed *and* the API has
  moved to a new window.
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
