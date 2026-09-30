"""Minimal internationalisation layer.

English is the source language: user-facing strings are written in English in
the code and wrapped in ``_()``. Every other language ships a catalog in
``claude_usage_tray/locales/<code>.py`` exposing a ``MESSAGES`` dict that maps
each English string to its translation. A missing entry falls back to English.

Adding a language: create ``locales/<code>.py`` and add ``<code>`` to
``SUPPORTED_LANGUAGES``. ``tests/test_i18n.py`` checks that every catalog
covers every string used in the code.
"""

from __future__ import annotations

import importlib
import os
import sys

SOURCE_LANGUAGE = "en"
SUPPORTED_LANGUAGES = ("en", "fr", "de", "es", "it", "pt")

# POSIX locale variables, in gettext precedence order.
LOCALE_VARIABLES = ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG")

_catalog: dict[str, str] = {}
_language = SOURCE_LANGUAGE


def _language_code(locale_name: str) -> str:
	"""Reduce a locale name such as ``fr_BE.UTF-8@euro`` to ``fr``."""
	return locale_name.split(".")[0].split("@")[0].split("_")[0].strip().lower()


def detect_language(environ: dict[str, str] | None = None) -> str:
	"""Return the first supported language found in the locale variables."""
	env = os.environ if environ is None else environ
	for variable in LOCALE_VARIABLES:
		# LANGUAGE may hold a colon-separated preference list.
		for entry in env.get(variable, "").split(":"):
			code = _language_code(entry)
			if code in ("c", "posix"):
				return SOURCE_LANGUAGE
			if code in SUPPORTED_LANGUAGES:
				return code
	return SOURCE_LANGUAGE


def set_language(language: str | None = None) -> str:
	"""Activate ``language`` (auto-detected when empty); return the code in use."""
	global _catalog, _language

	code = (language or "").strip().lower() or detect_language()
	if code not in SUPPORTED_LANGUAGES:
		print(
			f"claude-usage-tray: unsupported language {code!r}, "
			f"falling back to {SOURCE_LANGUAGE!r}",
			file=sys.stderr,
		)
		code = SOURCE_LANGUAGE

	if code == SOURCE_LANGUAGE:
		_catalog = {}
	else:
		module = importlib.import_module(f".locales.{code}", __package__)
		_catalog = module.MESSAGES
	_language = code
	return code


def current_language() -> str:
	return _language


def _(message: str) -> str:
	"""Translate ``message`` into the active language."""
	return _catalog.get(message, message)
