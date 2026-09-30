"""Firefox profile discovery tests, on throwaway directory trees."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from claude_usage_tray.cookie_reader import CookieError, find_profile


def make_install(root: Path, profile: str, cookies_mtime: float | None) -> Path:
	"""Create ``root/profiles.ini`` pointing at ``profile`` (+ cookies.sqlite)."""
	profile_dir = root / profile
	profile_dir.mkdir(parents=True)
	(root / "profiles.ini").write_text(
		f"[Profile0]\nName=default\nIsRelative=1\nPath={profile}\nDefault=1\n",
		encoding="utf-8",
	)
	if cookies_mtime is not None:
		cookies = profile_dir / "cookies.sqlite"
		cookies.write_bytes(b"")
		os.utime(cookies, (cookies_mtime, cookies_mtime))
	return profile_dir


class FindProfileTest(unittest.TestCase):
	def setUp(self) -> None:
		self._tmp = tempfile.TemporaryDirectory()
		self.base = Path(self._tmp.name)
		self.deb = self.base / "deb"
		self.snap = self.base / "snap"
		self.roots = (self.deb, self.snap)

	def tearDown(self) -> None:
		self._tmp.cleanup()

	def test_most_recently_used_install_wins(self) -> None:
		make_install(self.deb, "old.default", cookies_mtime=1_000)
		snap_profile = make_install(self.snap, "new.default", cookies_mtime=2_000)
		self.assertEqual(snap_profile, find_profile(None, self.roots))

	def test_single_install(self) -> None:
		deb_profile = make_install(self.deb, "only.default", cookies_mtime=None)
		self.assertEqual(deb_profile, find_profile(None, self.roots))

	def test_explicit_profile_searched_in_every_root(self) -> None:
		snap_profile = make_install(self.snap, "work", cookies_mtime=None)
		self.assertEqual(snap_profile, find_profile("work", self.roots))

	def test_nothing_found(self) -> None:
		with self.assertRaises(CookieError):
			find_profile(None, self.roots)
		with self.assertRaises(CookieError):
			find_profile("missing", self.roots)


if __name__ == "__main__":
	unittest.main()
