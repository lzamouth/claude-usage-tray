"""Formatting tests: progress bars, remaining time and reset labels."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from claude_usage_tray import i18n
from claude_usage_tray.api_client import WEEK, UsageWindow
from claude_usage_tray.formatting import format_bar, format_remaining, format_reset


class FormatRemainingTest(unittest.TestCase):
	def tearDown(self) -> None:
		i18n.set_language("en")

	def test_english(self) -> None:
		i18n.set_language("en")
		cases = [
			(timedelta(seconds=-30), "0 min"),
			(timedelta(minutes=48, seconds=59), "48 min"),
			(timedelta(hours=1), "1h 00m"),
			(timedelta(hours=3, minutes=20), "3h 20m"),
			(timedelta(days=5, hours=13, minutes=59), "5d 13h"),
		]
		for remaining, expected in cases:
			with self.subTest(remaining=remaining):
				self.assertEqual(expected, format_remaining(remaining))

	def test_french(self) -> None:
		i18n.set_language("fr")
		self.assertEqual("3 h 05", format_remaining(timedelta(hours=3, minutes=5)))
		self.assertEqual("2 j 4 h", format_remaining(timedelta(days=2, hours=4)))


class FormatBarTest(unittest.TestCase):
	NOW = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)

	def bar(self, utilization: float | None, elapsed: float | None) -> str | None:
		resets_at = None if elapsed is None else self.NOW + WEEK * (1 - elapsed)
		return format_bar(UsageWindow(utilization, resets_at), WEEK, self.NOW, cells=10)

	def test_zones(self) -> None:
		cases = [
			(20.0, 0.5, "██░░░▁▁▁▁▁"),  # under pace: margin up to the elapsed share
			(50.0, 0.2, "██▌▌▌▁▁▁▁▁"),  # ahead of pace: striped excess
			(30.0, 0.3, "███▁▁▁▁▁▁▁"),  # exactly on pace
			(0.0, 0.4, "░░░░▁▁▁▁▁▁"),
			(120.0, 1.0, "██████████"),  # clamped to the bar
			(40.0, None, "████▁▁▁▁▁▁"),  # unknown reset: plain usage bar
		]
		for utilization, elapsed, expected in cases:
			with self.subTest(utilization=utilization, elapsed=elapsed):
				self.assertEqual(expected, self.bar(utilization, elapsed))

	def test_no_usage(self) -> None:
		self.assertIsNone(self.bar(None, 0.5))
		self.assertIsNone(format_bar(None, WEEK, self.NOW))


class FormatResetTest(unittest.TestCase):
	def tearDown(self) -> None:
		i18n.set_language("en")

	def test_reset_label(self) -> None:
		now = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)
		resets_at = now + timedelta(hours=3, minutes=20)
		local = resets_at.astimezone()
		window = UsageWindow(10.0, resets_at)

		i18n.set_language("en")
		weekday = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")[local.weekday()]
		self.assertEqual(
			f"reset in 3h 20m ({weekday} {local:%H:%M})", format_reset(window, now)
		)
		self.assertEqual("unknown reset", format_reset(UsageWindow(10.0, None), now))


if __name__ == "__main__":
	unittest.main()
