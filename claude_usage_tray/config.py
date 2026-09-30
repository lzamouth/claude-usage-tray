"""Configuration: paths and default settings."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

if sys.version_info >= (3, 11):
	import tomllib
else:  # pragma: no cover - fallback for old Python
	import tomli as tomllib

CONFIG_DIR = Path.home() / ".config" / "claude-usage-tray"
CONFIG_PATH = CONFIG_DIR / "config.toml"

DEFAULT_CONFIG_TOML = """\
# claude-usage-tray configuration
# Refresh interval, in seconds (recommended: 300-600)
poll_interval_seconds = 300

# Firefox profile holding the claude.ai session cookie.
# Leave empty to auto-detect the default profile.
firefox_profile = ""

# Interface language: "en", "fr", or empty to follow the system locale.
language = ""
"""


@dataclass(frozen=True)
class Config:
	poll_interval_seconds: int
	firefox_profile: str | None
	language: str | None


def load_config() -> Config:
	"""Load the user config, creating the default file if it does not exist."""
	if not CONFIG_PATH.exists():
		CONFIG_DIR.mkdir(parents=True, exist_ok=True)
		CONFIG_PATH.write_text(DEFAULT_CONFIG_TOML, encoding="utf-8")
		data = tomllib.loads(DEFAULT_CONFIG_TOML)
	else:
		data = tomllib.loads(CONFIG_PATH.read_text(encoding="utf-8"))

	poll_interval = int(data.get("poll_interval_seconds", 300))
	profile = data.get("firefox_profile") or None
	language = data.get("language") or None

	return Config(
		poll_interval_seconds=poll_interval,
		firefox_profile=profile,
		language=language,
	)
