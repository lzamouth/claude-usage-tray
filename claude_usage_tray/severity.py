"""How worrying a usage figure is: absolute thresholds plus pace.

Kept free of GTK so that the policy can be unit-tested.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import IntEnum

from .api_client import FIVE_HOURS, WEEK, UsageSnapshot, UsageWindow

WARN_THRESHOLD = 75.0
CRITICAL_THRESHOLD = 90.0

# Pace alert: usage is ahead of the clock by at least PACE_MARGIN points
# (e.g. 40 % used when only 25 % of the window has elapsed). Ignored below
# PACE_MIN_UTILIZATION, where early-window noise would trigger it right
# after every reset.
PACE_MARGIN = 10.0
PACE_MIN_UTILIZATION = 25.0


class Severity(IntEnum):
	OK = 0
	WARN = 1
	CRITICAL = 2


def is_ahead_of_pace(
	window: UsageWindow, period: timedelta, now: datetime | None = None
) -> bool:
	"""True if usage clearly outpaces the time elapsed in the window."""
	if window.utilization is None or window.utilization < PACE_MIN_UTILIZATION:
		return False
	elapsed = window.elapsed_fraction(period, now)
	if elapsed is None:
		return False
	return window.utilization >= elapsed * 100 + PACE_MARGIN


def window_severity(
	window: UsageWindow | None, period: timedelta, now: datetime | None = None
) -> Severity:
	if window is None or window.utilization is None:
		return Severity.OK
	if window.utilization >= CRITICAL_THRESHOLD:
		return Severity.CRITICAL
	if window.utilization >= WARN_THRESHOLD or is_ahead_of_pace(window, period, now):
		return Severity.WARN
	return Severity.OK


def snapshot_severity(snapshot: UsageSnapshot, now: datetime | None = None) -> Severity:
	"""Worst severity across every window: 5 hours, 7 days and per model."""
	severities = [
		window_severity(snapshot.five_hour, FIVE_HOURS, now),
		window_severity(snapshot.seven_day, WEEK, now),
	]
	severities += [
		window_severity(window, WEEK, now) for window in snapshot.model_breakdown.values()
	]
	return max(severities)
