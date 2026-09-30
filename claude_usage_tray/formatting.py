"""Text formatting of usage figures, shared by the menu and notifications.

Kept free of GTK so that it can be unit-tested.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .api_client import FIVE_HOURS, WEEK, UsageWindow
from .i18n import _

# Display names for known models (proper nouns, not translated); an unknown
# model falls back to its capitalised key (e.g. "fable" -> "Fable").
MODEL_LABELS = {
	"sonnet": "Sonnet",
	"opus": "Opus",
	"haiku": "Haiku",
	"fable": "Fable",
}

# Preferred display order; models missing from this list follow, sorted
# alphabetically.
MODEL_ORDER = ["sonnet", "opus", "haiku", "fable"]

# Weekday abbreviations, indexed by datetime.weekday(). Translated at use
# time rather than via strftime("%a"), which depends on the C locale.
WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def model_label(key: str) -> str:
	return MODEL_LABELS.get(key, key.replace("_", " ").capitalize())


def sorted_model_keys(model_breakdown: dict[str, UsageWindow]) -> list[str]:
	known = [key for key in MODEL_ORDER if key in model_breakdown]
	unknown = sorted(key for key in model_breakdown if key not in MODEL_ORDER)
	return known + unknown


def format_percent(window: UsageWindow | None) -> str:
	if window is None or window.utilization is None:
		return "—"
	return f"{window.utilization:.0f}%"


def _format_decimal(value: float) -> str:
	# "." is translated to the locale's decimal separator.
	return f"{value:.1f}".replace(".", _("."))


def _format_pace(
	window: UsageWindow | None, period: timedelta, unit: timedelta, template: str
) -> str:
	"""Usage and elapsed time of a window, both expressed in ``unit``.

	Putting them in the same unit makes it obvious whether usage is ahead of
	or behind the clock: "1.1 d / 1.3 d elapsed" means under pace.
	"""
	if window is None or window.utilization is None:
		return format_percent(window)
	elapsed = window.elapsed_fraction(period)
	if elapsed is None:
		return format_percent(window)
	units = period / unit
	return template.format(
		percent=format_percent(window),
		used=_format_decimal(window.utilization / 100 * units),
		elapsed=_format_decimal(elapsed * units),
	)


def format_session_pace(window: UsageWindow | None) -> str:
	"""5-hour window pace, in hours."""
	return _format_pace(
		window, FIVE_HOURS, timedelta(hours=1), _("{percent} ({used} h / {elapsed} h elapsed)")
	)


def format_weekly_pace(window: UsageWindow | None) -> str:
	"""Weekly window pace, in days."""
	return _format_pace(
		window, WEEK, timedelta(days=1), _("{percent} ({used} d / {elapsed} d elapsed)")
	)


def format_remaining(remaining: timedelta) -> str:
	"""Compact duration: "48 min", "3h 20m", "5d 13h" (negative counts as 0)."""
	minutes_total = max(0, int(remaining.total_seconds() // 60))
	days, minutes_left = divmod(minutes_total, 24 * 60)
	hours, minutes = divmod(minutes_left, 60)
	if days:
		return _("{days}d {hours}h").format(days=days, hours=hours)
	if hours:
		return _("{hours}h {minutes:02d}m").format(hours=hours, minutes=minutes)
	return _("{minutes} min").format(minutes=minutes)


def format_reset(window: UsageWindow | None, now: datetime | None = None) -> str:
	"""Time left before the reset, then its local weekday and time.

	The date itself is left out: windows last at most a week, so the
	remaining time already tells which weekday is meant.
	"""
	if window is None or window.resets_at is None:
		return _("unknown reset")
	now = now or datetime.now(timezone.utc)
	local = window.resets_at.astimezone()
	when = f"{_(WEEKDAYS[local.weekday()])} {local.strftime('%H:%M')}"
	return _("reset in {remaining} ({when})").format(
		remaining=format_remaining(window.resets_at - now), when=when
	)
