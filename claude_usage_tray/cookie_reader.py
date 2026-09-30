"""Extraction of the claude.ai session cookie from the Firefox profile."""

from __future__ import annotations

import configparser
import shutil
import sqlite3
import tempfile
import time
from pathlib import Path

from .i18n import _

# Where Firefox keeps its profiles, depending on how it was installed.
FIREFOX_ROOTS = (
	# .deb package or tarball
	Path.home() / ".mozilla" / "firefox",
	# XDG layout used by recent Firefox versions for new installs
	Path.home() / ".config" / "mozilla" / "firefox",
	# snap (Ubuntu's default)
	Path.home() / "snap" / "firefox" / "common" / ".mozilla" / "firefox",
	# Flatpak
	Path.home() / ".var" / "app" / "org.mozilla.firefox" / ".mozilla" / "firefox",
)
COOKIE_NAME = "sessionKey"
COOKIE_HOSTS = ("claude.ai", ".claude.ai")


class CookieError(RuntimeError):
	"""The session cookie could not be found or read."""


def _default_profile(root: Path) -> Path | None:
	"""Default profile listed in ``root/profiles.ini``, if any."""
	profiles_ini = root / "profiles.ini"
	if not profiles_ini.is_file():
		return None

	parser = configparser.ConfigParser()
	parser.read(profiles_ini, encoding="utf-8")

	# 1) A [Profile*] section flagged Default=1.
	for section in parser.sections():
		if section.startswith("Profile") and parser.getboolean(
			section, "Default", fallback=False
		):
			return root / parser.get(section, "Path")

	# 2) The [Install*] section pointing at the current default profile.
	for section in parser.sections():
		if section.startswith("Install") and parser.has_option(section, "Default"):
			return root / parser.get(section, "Default")

	# 3) Fallback: first listed profile.
	for section in parser.sections():
		if section.startswith("Profile") and parser.has_option(section, "Path"):
			return root / parser.get(section, "Path")

	return None


def _cookie_db_mtime(profile_dir: Path) -> float:
	try:
		return (profile_dir / "cookies.sqlite").stat().st_mtime
	except OSError:
		return 0.0


def find_profile(
	explicit_profile: str | None = None, roots: tuple[Path, ...] = FIREFOX_ROOTS
) -> Path:
	"""Return the Firefox profile directory to use.

	Without an explicit profile, the default profile of every Firefox
	installation found is considered, and the one whose cookie database was
	written most recently wins — so a leftover ~/.mozilla from a previous
	.deb install does not shadow the snap actually in use.
	"""
	if explicit_profile:
		for root in roots:
			if (root / explicit_profile).is_dir():
				return root / explicit_profile
		# Also accept an absolute path.
		profile_dir = Path(explicit_profile).expanduser()
		if not profile_dir.is_dir():
			raise CookieError(
				_("Firefox profile not found: {profile}").format(profile=explicit_profile)
			)
		return profile_dir

	candidates = [profile for root in roots if (profile := _default_profile(root))]
	if not candidates:
		raise CookieError(
			_(
				"No Firefox profile found. Is Firefox installed and has it "
				"been started at least once?"
			)
		)
	return max(candidates, key=_cookie_db_mtime)


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
