"""Notification decisions: thresholds crossed once, resets only when useful."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from claude_usage_tray.api_client import UsageSnapshot, UsageWindow
from claude_usage_tray.notifications import UsageWatcher

NOW = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)
FIVE_HOUR_RESET = NOW + timedelta(hours=2)
WEEK_RESET = NOW + timedelta(days=5)


def snapshot(
	five_hour: float | None,
	seven_day: float = 10.0,
	five_hour_reset: datetime | None = FIVE_HOUR_RESET,
	models: dict[str, float] | None = None,
) -> UsageSnapshot:
	return UsageSnapshot(
		five_hour=UsageWindow(five_hour, five_hour_reset),
		seven_day=UsageWindow(seven_day, WEEK_RESET),
		model_breakdown={k: UsageWindow(v, WEEK_RESET) for k, v in (models or {}).items()},
	)


class UsageWatcherTest(unittest.TestCase):
	def setUp(self) -> None:
		self.watcher = UsageWatcher()

	def feed(self, snap: UsageSnapshot, now: datetime = NOW) -> list[str]:
		return [f"{n.key}:{'critical' if n.critical else n.icon}" for n in self.watcher.update(snap, now)]

	def test_first_snapshot_is_a_baseline(self) -> None:
		self.assertEqual([], self.feed(snapshot(97.0)))

	def test_threshold_crossed_once(self) -> None:
		self.feed(snapshot(70.0))
		self.assertEqual(["five_hour:dialog-warning"], self.feed(snapshot(82.0)))
		self.assertEqual([], self.feed(snapshot(85.0)))
		self.assertEqual(["five_hour:critical"], self.feed(snapshot(96.0)))
		self.assertEqual([], self.feed(snapshot(99.0)))

	def test_jump_over_both_thresholds_gives_one_critical_notice(self) -> None:
		self.feed(snapshot(50.0))
		self.assertEqual(["five_hour:critical"], self.feed(snapshot(97.0)))

	def test_weekly_and_model_windows(self) -> None:
		self.feed(snapshot(10.0, seven_day=70.0, models={"fable": 90.0}))
		notices = self.feed(snapshot(10.0, seven_day=81.0, models={"fable": 95.0}))
		self.assertEqual(["seven_day:dialog-warning", "model:fable:critical"], notices)

	def test_reset_notified_once_when_limit_was_high(self) -> None:
		self.feed(snapshot(90.0))
		after = FIVE_HOUR_RESET + timedelta(minutes=2)
		# The API still returns the old window: nothing yet.
		self.assertEqual([], self.feed(snapshot(90.0), after))
		new_reset = after + timedelta(hours=5)
		self.assertEqual(
			["five_hour:dialog-information"],
			self.feed(snapshot(1.0, five_hour_reset=new_reset), after),
		)
		self.assertEqual([], self.feed(snapshot(2.0, five_hour_reset=new_reset), after))

	def test_reset_not_notified_when_limit_was_low(self) -> None:
		self.feed(snapshot(30.0))
		after = FIVE_HOUR_RESET + timedelta(minutes=2)
		self.assertEqual([], self.feed(snapshot(0.0, five_hour_reset=None), after))

	def test_threshold_counted_again_in_a_new_window(self) -> None:
		self.feed(snapshot(85.0))
		after = FIVE_HOUR_RESET + timedelta(minutes=2)
		new_reset = after + timedelta(hours=5)
		# Reset notice, then the new window is already past 80 %.
		self.assertEqual(
			["five_hour:dialog-information", "five_hour:dialog-warning"],
			self.feed(snapshot(81.0, five_hour_reset=new_reset), after),
		)


if __name__ == "__main__":
	unittest.main()
