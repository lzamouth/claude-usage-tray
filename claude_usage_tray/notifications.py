"""Desktop notifications: usage thresholds crossed and limits reset.

``UsageWatcher`` decides what to notify by comparing successive snapshots
(pure logic, unit-tested); ``DesktopNotifier`` sends it through the
freedesktop notification service over D-Bus, with no extra dependency.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from gi.repository import Gio, GLib

from .api_client import UsageSnapshot, UsageWindow
from .formatting import format_percent, format_reset, model_label
from .i18n import _

# Usage levels (percent) that trigger a notification when crossed upwards.
NOTIFY_THRESHOLDS = (80.0, 95.0)

# A reset is only worth notifying if the limit was actually getting in the
# way; otherwise the 5-hour window would ping every few hours.
RESET_NOTIFY_MIN_UTILIZATION = NOTIFY_THRESHOLDS[0]

# resets_at jitters by a few microseconds between calls; a new window moves
# it by hours.
RESET_TOLERANCE = timedelta(minutes=1)

APP_NAME = "Claude Usage Tray"
DESKTOP_ENTRY = "claude-usage-tray"
ICON_WARNING = "dialog-warning"
ICON_INFO = "dialog-information"

URGENCY_NORMAL = 1
URGENCY_CRITICAL = 2


@dataclass(frozen=True)
class Notice:
	# Window key: a newer notice for the same window replaces the older one.
	key: str
	summary: str
	body: str
	critical: bool = False
	icon: str = ICON_WARNING


def _named_windows(snapshot: UsageSnapshot) -> dict[str, tuple[str, UsageWindow | None]]:
	"""Every window of a snapshot, keyed by a stable id, with its display name."""
	windows: dict[str, tuple[str, UsageWindow | None]] = {
		"five_hour": (_("5 hours"), snapshot.five_hour),
		"seven_day": (_("7 days"), snapshot.seven_day),
	}
	for key, window in snapshot.model_breakdown.items():
		windows[f"model:{key}"] = (
			_("7 days ({model})").format(model=model_label(key)),
			window,
		)
	return windows


def _has_reset(old: UsageWindow | None, new: UsageWindow | None, now: datetime) -> bool:
	"""True once the old window's reset time has passed and a new window began."""
	if old is None or old.resets_at is None or now < old.resets_at:
		return False
	# The API may keep returning the old window for a moment after the reset;
	# wait until it actually moves on, so the reset is reported only once.
	if new is None or new.resets_at is None:
		return True
	return new.resets_at > old.resets_at + RESET_TOLERANCE


def _sentence(text: str) -> str:
	return text[:1].upper() + text[1:]


class UsageWatcher:
	"""Turns successive usage snapshots into notices."""

	def __init__(self) -> None:
		self._previous: UsageSnapshot | None = None

	def update(self, snapshot: UsageSnapshot, now: datetime | None = None) -> list[Notice]:
		previous, self._previous = self._previous, snapshot
		# The first snapshot is only a baseline: restarting the applet (e.g.
		# at every login) must not repeat notifications already shown.
		if previous is None:
			return []

		now = now or datetime.now(timezone.utc)
		old_windows = _named_windows(previous)
		notices: list[Notice] = []

		for key, (name, window) in _named_windows(snapshot).items():
			old = old_windows.get(key, (name, None))[1]
			reset = _has_reset(old, window, now)

			if (
				reset
				and old.utilization is not None
				and old.utilization >= RESET_NOTIFY_MIN_UTILIZATION
			):
				notices.append(
					Notice(
						key=key,
						summary=_("Claude: {window} limit reset").format(window=name),
						body=_("Usage is available again."),
						icon=ICON_INFO,
					)
				)

			if window is None or window.utilization is None:
				continue
			old_utilization = 0.0
			if not reset and old is not None and old.utilization is not None:
				old_utilization = old.utilization
			crossed = [
				level for level in NOTIFY_THRESHOLDS if old_utilization < level <= window.utilization
			]
			if crossed:
				notices.append(
					Notice(
						key=key,
						summary=_("Claude: {window} limit at {percent}").format(
							window=name, percent=format_percent(window)
						),
						body=_sentence(format_reset(window, now)),
						critical=crossed[-1] >= NOTIFY_THRESHOLDS[-1],
					)
				)

		return notices


class DesktopNotifier:
	"""Sends notices through org.freedesktop.Notifications (main thread only)."""

	def __init__(self) -> None:
		# Notification id per window key, so that a newer notice replaces the
		# previous one instead of piling up.
		self._ids: dict[str, int] = {}
		try:
			self._proxy: Gio.DBusProxy | None = Gio.DBusProxy.new_for_bus_sync(
				Gio.BusType.SESSION,
				Gio.DBusProxyFlags.DO_NOT_LOAD_PROPERTIES,
				None,
				"org.freedesktop.Notifications",
				"/org/freedesktop/Notifications",
				"org.freedesktop.Notifications",
				None,
			)
		except GLib.Error:
			self._proxy = None

	def send(self, notice: Notice) -> None:
		if self._proxy is None:
			return
		hints = {
			"desktop-entry": GLib.Variant("s", DESKTOP_ENTRY),
			# Critical notifications stay on screen until dismissed.
			"urgency": GLib.Variant("y", URGENCY_CRITICAL if notice.critical else URGENCY_NORMAL),
		}
		try:
			result = self._proxy.call_sync(
				"Notify",
				GLib.Variant(
					"(susssasa{sv}i)",
					(
						APP_NAME,
						self._ids.get(notice.key, 0),
						notice.icon,
						notice.summary,
						notice.body,
						[],
						hints,
						-1,
					),
				),
				Gio.DBusCallFlags.NONE,
				-1,
				None,
			)
		except GLib.Error:
			# No notification service running: the icon still shows it all.
			return
		(self._ids[notice.key],) = result.unpack()
