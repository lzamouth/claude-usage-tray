# claude-usage-tray

**English** · [Français](README.fr.md)

Linux systray indicator (GNOME / KDE) showing your claude.ai plan usage:

- the icon label shows the **5-hour** session usage;
- the menu shows the **7-day** usage, the per-model weekly limits the API
  reports (e.g. Fable, Opus, Sonnet), and when each window resets;
- the icon turns to a warning (≥ 75 %) or error (≥ 90 %) symbol as you get
  close to the limit.

The interface is available in **English** and **French** (see
[Language](#language)).

> [!WARNING]
> This tool relies on the **undocumented internal API** that the claude.ai
> website itself calls. It may change or be blocked without notice. It is
> an unofficial project, not affiliated with or endorsed by Anthropic.

## How it works

- **No secret is stored.** The applet reads the `sessionKey` cookie that
  Firefox already holds after you sign in to claude.ai normally, straight
  from the profile's `cookies.sqlite` (copied to a temp dir, since Firefox
  locks it). Only the default container is used; expired cookies are
  ignored.
- Every 5 minutes (configurable) it calls:
  - `GET https://claude.ai/api/organizations`
  - `GET https://claude.ai/api/organizations/{id}/usage`
- On repeated failures the interval doubles (up to 1 hour) instead of
  hammering the server; it returns to normal on the first success.

## Requirements

- Linux with **Firefox**, signed in to claude.ai.
- Python ≥ 3.11, GTK 3 and an AppIndicator library:

```bash
sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1
```

- **GNOME** does not show systray icons out of the box. Install and enable
  the *AppIndicator and KStatusNotifierItem Support* extension, then log out
  and back in:

```bash
sudo apt install gnome-shell-extension-appindicator
```

- **KDE Plasma** shows StatusNotifierItem icons natively.

## Installation

```bash
git clone https://github.com/lzamouth/claude-usage-tray.git
cd claude-usage-tray
./install.sh
```

`install.sh` creates a virtualenv (with `--system-site-packages`, because
`python3-gi` comes from the distribution) and adds an autostart entry. Use
`./install.sh --systemd` for a systemd user service instead (restarted on
crash), or `--no-start` to only set up the virtualenv.

Run it in the foreground (useful for debugging):

```bash
./.venv/bin/python -m claude_usage_tray
```

## Configuration

Created on first run at `~/.config/claude-usage-tray/config.toml`:

```toml
poll_interval_seconds = 300   # refresh interval
firefox_profile = ""          # empty = default Firefox profile
language = ""                 # "en", "fr", or empty = system locale
```

### Language

With `language = ""`, the language follows the usual locale variables
(`LANGUAGE`, `LC_ALL`, `LC_MESSAGES`, `LANG`); unsupported languages fall back
to English.

To add a language, create `claude_usage_tray/locales/<code>.py` (copy
`fr.py`), add the code to `SUPPORTED_LANGUAGES` in `claude_usage_tray/i18n.py`,
and run the tests — they fail if a string is missing or a placeholder differs.

## Troubleshooting

Run the diagnostic script first — it shows the cookie rows found, a request
without browser headers, and a request made exactly like the applet:

```bash
./.venv/bin/python diag_usage.py
```

| Menu message | Meaning |
|---|---|
| *sessionKey cookie not found* | Not signed in to claude.ai in Firefox, or wrong profile (`firefox_profile`). |
| *cookie has expired* / *rejected the session* | Sign in again; the **Sign in to Claude again…** menu item opens Firefox and polls quickly until it works. |
| *Blocked by Cloudflare* | Anti-bot challenge, unrelated to your session: signing in again won't help. The applet backs off automatically. |
| Icon missing on GNOME | The AppIndicator extension is not installed or not enabled. |

## Development

```bash
./.venv/bin/python -m unittest discover -s tests -t .
```

See [CLAUDE.md](CLAUDE.md) for the architecture and code conventions.

## Authorship

The code of this project was written by **Claude**, Anthropic's AI model,
working in [Claude Code](https://claude.com/claude-code), at the request of
and published by [@lzamouth](https://github.com/lzamouth).

## License

[MIT](LICENSE)
