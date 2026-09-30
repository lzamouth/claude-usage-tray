"""Severity policy tests: absolute thresholds, pace alert, worst window wins."""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

from claude_usage_tray.api_client import FIVE_HOURS, WEEK, UsageSnapshot, UsageWindow
from claude_usage_tray.severity import (
	Severity,
	is_ahead_of_pace,
	snapshot_severity,
	window_severity,
)

NOW = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)


def weekly(utilization: float | None, elapsed: float) -> UsageWindow:
	"""Weekly window with ``elapsed`` (0-1) of its duration already gone."""
	return UsageWindow(utilization, NOW + WEEK * (1 - elapsed))


class PaceTest(unittest.TestCase):
	def test_ahead_of_pace(self) -> None:
		cases = [
			(40.0, 0.25, True),  # 15 points ahead
			(35.0, 0.25, True),  # exactly PACE_MARGIN ahead
			(30.0, 0.25, False),  # within the margin
			(20.0, 0.05, False),  # below PACE_MIN_UTILIZATION
			(60.0, 0.70, False),  # behind the clock
		]
		for utilization, elapsed, expected in cases:
			with self.subTest(utilization=utilization, elapsed=elapsed):
				self.assertIs(expected, is_ahead_of_pace(weekly(utilization, elapsed), WEEK, NOW))

	def test_unknown_reset_is_not_ahead(self) -> None:
		self.assertFalse(is_ahead_of_pace(UsageWindow(80.0, None), WEEK, NOW))


class WindowSeverityTest(unittest.TestCase):
	def test_thresholds(self) -> None:
		cases = [
			(None, Severity.OK),
			(50.0, Severity.OK),
			(75.0, Severity.WARN),
			(90.0, Severity.CRITICAL),
		]
		for utilization, expected in cases:
			with self.subTest(utilization=utilization):
				# Late in the window, so pace never triggers here.
				self.assertEqual(expected, window_severity(weekly(utilization, 0.95), WEEK, NOW))

	def test_pace_warns_below_threshold(self) -> None:
		self.assertEqual(Severity.WARN, window_severity(weekly(50.0, 0.2), WEEK, NOW))


class SnapshotSeverityTest(unittest.TestCase):
	def test_weekly_limit_drives_icon_when_session_is_low(self) -> None:
		snapshot = UsageSnapshot(
			five_hour=UsageWindow(5.0, NOW + FIVE_HOURS / 2),
			seven_day=weekly(92.0, 0.9),
			model_breakdown={},
		)
		self.assertEqual(Severity.CRITICAL, snapshot_severity(snapshot, NOW))

	def test_model_limit_counts(self) -> None:
		snapshot = UsageSnapshot(
			five_hour=UsageWindow(5.0, NOW + FIVE_HOURS / 2),
			seven_day=weekly(30.0, 0.9),
			model_breakdown={"fable": weekly(80.0, 0.9)},
		)
		self.assertEqual(Severity.WARN, snapshot_severity(snapshot, NOW))

	def test_all_quiet(self) -> None:
		snapshot = UsageSnapshot(
			five_hour=UsageWindow(5.0, NOW + FIVE_HOURS / 2),
			seven_day=weekly(30.0, 0.5),
			model_breakdown={"fable": weekly(10.0, 0.5)},
		)
		self.assertEqual(Severity.OK, snapshot_severity(snapshot, NOW))


if __name__ == "__main__":
	unittest.main()
