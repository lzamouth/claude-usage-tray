"""Extraction of the claude.ai session cookie from the Firefox profile."""

from __future__ import annotations

import configparser
import shutil
import sqlite3
import tempfile
import time
from pathlib import Path

from .i18n import _

FIREFOX_ROOT = Path.home() / ".mozilla" / "firefox"
COOKIE_NAME = "sessionKey"
COOKIE_HOSTS = ("claude.ai", ".claude.ai")


class CookieError(RuntimeError):
	"""The session cookie could not be found or read."""


def find_profile(explicit_profile: str | None = None) -> Path:
	"""Return the Firefox profile directory to use."""
	if explicit_profile:
		profile_dir = FIREFOX_ROOT / explicit_profile
		if not profile_dir.is_dir():
			# Also accept an absolute path.
			profile_dir = Path(explicit_profile).expanduser()
		if not profile_dir.is_dir():
			raise CookieError(
				_("Firefox profile not found: {profile}").format(profile=explicit_profile)
			)
		return profile_dir

	profiles_ini = FIREFOX_ROOT / "profiles.ini"
	if not profiles_ini.is_file():
		raise CookieError(
			_(
				"profiles.ini not found ({path}). Is Firefox installed and has "
				"it been started at least once?"
			).format(path=profiles_ini)
		)

	parser = configparser.ConfigParser()
	parser.read(profiles_ini, encoding="utf-8")

	# 1) A [Profile*] section flagged Default=1.
	for section in parser.sections():
		if section.startswith("Profile") and parser.getboolean(
			section, "Default", fallback=False
		):
			return FIREFOX_ROOT / parser.get(section, "Path")

	# 2) The [Install*] section pointing at the current default profile.
	for section in parser.sections():
		if section.startswith("Install") and parser.has_option(section, "Default"):
			return FIREFOX_ROOT / parser.get(section, "Default")

	# 3) Fallback: first listed profile.
	for section in parser.sections():
		if section.startswith("Profile") and parser.has_option(section, "Path"):
			return FIREFOX_ROOT / parser.get(section, "Path")

	raise CookieError(_("No Firefox profile found in profiles.ini."))


def copy_cookie_db(profile_dir: Path, dest_dir: Path) -> Path:
	"""Copy cookies.sqlite (+ WAL/SHM), since Firefox locks the original."""
	src = profile_dir / "cookies.sqlite"
	if not src.is_file():
		raise CookieError(_("cookies.sqlite not found in {path}").format(path=profile_dir))

	dest = dest_dir / "cookies.sqlite"
	shutil.copy2(src, dest)

	for suffix in ("-wal", "-shm"):
		companion = profile_dir / f"cookies.sqlite{suffix}"
		if companion.is_file():
			shutil.copy2(companion, dest_dir / f"cookies.sqlite{suffix}")

	return dest


def expiry_seconds(expiry: int | None) -> float | None:
	"""Normalise moz_cookies.expiry to seconds (recent Firefox uses milliseconds)."""
	if not expiry:
		return None
	return expiry / 1000 if expiry > 10**11 else float(expiry)


def read_session_key(explicit_profile: str | None = None) -> str:
	"""Read the claude.ai sessionKey cookie from the default Firefox profile.

	The cookies.sqlite database is copied to a temporary directory first to
	avoid lock conflicts with a running Firefox.

	Only cookies from the default container (empty originAttributes: neither
	a Firefox container nor private browsing) that have not expired are kept.
	"""
	profile_dir = find_profile(explicit_profile)

	with tempfile.TemporaryDirectory(prefix="claude-usage-tray-") as tmp:
		db_path = copy_cookie_db(profile_dir, Path(tmp))

		placeholders = ",".join("?" for _host in COOKIE_HOSTS)
		query = (
			f"SELECT value, expiry FROM moz_cookies "
			f"WHERE name = ? AND host IN ({placeholders}) "
			f"AND originAttributes = '' "
			f"ORDER BY lastAccessed DESC"
		)

		conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
		try:
			rows = conn.execute(query, (COOKIE_NAME, *COOKIE_HOSTS)).fetchall()
		finally:
			conn.close()

	now = time.time()
	valid = [
		value
		for value, expiry in rows
		if value and ((exp := expiry_seconds(expiry)) is None or exp > now)
	]

	if not valid:
		if rows:
			raise CookieError(
				_(
					"The claude.ai sessionKey cookie has expired — sign in to "
					"claude.ai again in Firefox."
				)
			)
		raise CookieError(
			_(
				"sessionKey cookie not found for claude.ai — are you signed in "
				"to claude.ai in Firefox?"
			)
		)

	# On duplicates (claude.ai and .claude.ai hosts), the most recently used
	# cookie wins.
	return valid[0]
