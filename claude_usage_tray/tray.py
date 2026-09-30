"""Systray icon and menu (StatusNotifierItem protocol via AppIndicator)."""

from __future__ import annotations

import shutil
import subprocess
from datetime import timedelta

import gi

gi.require_version("Gtk", "3.0")

try:
	gi.require_version("AyatanaAppIndicator3", "0.1")
	from gi.repository import AyatanaAppIndicator3 as AppIndicator3
except (ValueError, ImportError):
	gi.require_version("AppIndicator3", "0.1")
	from gi.repository import AppIndicator3

from gi.repository import GLib, Gtk

from .api_client import WEEK, UsageSnapshot, UsageWindow
from .i18n import _

APP_ID = "claude-usage-tray"
LOGIN_URL = "https://claude.ai/login"
ICON_OK = "network-transmit-receive-symbolic"
ICON_WARN = "dialog-warning-symbolic"
ICON_ERROR = "dialog-error-symbolic"

WARN_THRESHOLD = 75.0
CRITICAL_THRESHOLD = 90.0

# Menu slots reserved for the per-model breakdown — generous, so that new
# models added on claude.ai fit without touching the code.
MAX_MODEL_ROWS = 6

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


def open_login_page() -> None:
	"""Open the claude.ai sign-in page in Firefox.

	The session cookie is read from the Firefox profile, so Firefox is
	preferred explicitly; the default browser is the fallback when the
	executable cannot be found.
	"""
	firefox = shutil.which("firefox")
	command = [firefox, LOGIN_URL] if firefox else ["xdg-open", LOGIN_URL]
	try:
		subprocess.Popen(
			command,
			stdout=subprocess.DEVNULL,
			stderr=subprocess.DEVNULL,
			start_new_session=True,
		)
	except OSError:
		# Last resort: let GTK resolve the default handler.
		try:
			Gtk.show_uri_on_window(None, LOGIN_URL, Gtk.get_current_event_time())
		except Exception:
			pass


def _model_label(suffix: str) -> str:
	return MODEL_LABELS.get(suffix, suffix.replace("_", " ").capitalize())


def _sorted_model_keys(model_breakdown: dict[str, UsageWindow]) -> list[str]:
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


def format_weekly_pace(window: UsageWindow) -> str:
	"""Usage and elapsed time of a weekly window, both in days.

	Putting them in the same unit makes it obvious whether usage is ahead of
	or behind the clock: "1.1 d / 1.3 d elapsed" means under pace.
	"""
	elapsed = window.elapsed_fraction(WEEK)
	if window.utilization is None or elapsed is None:
		return format_percent(window)
	week_days = WEEK / timedelta(days=1)
	return _("{percent} ({used} d / {elapsed} d elapsed)").format(
		percent=format_percent(window),
		used=_format_decimal(window.utilization / 100 * week_days),
		elapsed=_format_decimal(elapsed * week_days),
	)


def format_reset(window: UsageWindow | None) -> str:
	if window is None or window.resets_at is None:
		return _("unknown reset")
	local = window.resets_at.astimezone()
	weekday = _(WEEKDAYS[local.weekday()])
	# Date/time pattern is translatable: day and month order differ by locale.
	when = f"{weekday} {local.strftime(_('%m/%d %H:%M'))}"
	return _("reset {when}").format(when=when)


class UsageTray:
	"""Wraps the systray indicator and keeps its menu up to date."""

	def __init__(self, on_refresh_requested, on_quit, on_login_requested=None) -> None:
		self._on_refresh_requested = on_refresh_requested
		self._on_quit = on_quit
		self._on_login_requested = on_login_requested or open_login_page

		self._indicator = AppIndicator3.Indicator.new(
			APP_ID, ICON_OK, AppIndicator3.IndicatorCategory.APPLICATION_STATUS
		)
		self._indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

		self._header_item = Gtk.MenuItem(label=_("Claude — loading…"))
		self._header_item.set_sensitive(False)

		self._detail_items: list[Gtk.MenuItem] = []
		self._status_item = Gtk.MenuItem(label="")
		self._status_item.set_sensitive(False)
		self._status_item.set_no_show_all(True)
		self._status_item.set_visible(False)

		self._login_item = Gtk.MenuItem(label=_("Sign in to Claude again…"))
		self._login_item.set_no_show_all(True)
		self._login_item.set_visible(False)

		self._menu = Gtk.Menu()
		self._build_static_menu()
		self._indicator.set_menu(self._menu)

	def _build_static_menu(self) -> None:
		self._menu.append(self._header_item)
		self._menu.append(Gtk.SeparatorMenuItem())

		# Slots for the details (overall 7 days + per model), filled in
		# dynamically. The 5-hour figure is shown on the systray icon itself.
		for _index in range(1 + MAX_MODEL_ROWS):
			item = Gtk.MenuItem(label="")
			self._menu.append(item)
			self._detail_items.append(item)

		self._menu.append(Gtk.SeparatorMenuItem())
		self._menu.append(self._status_item)

		refresh_item = Gtk.MenuItem(label=_("Refresh now"))
		refresh_item.connect("activate", lambda _item: self._on_refresh_requested())
		self._menu.append(refresh_item)

		# Only shown when the session is expired or missing.
		self._login_item.connect("activate", lambda _item: self._on_login_requested())
		self._menu.append(self._login_item)

		self._menu.append(Gtk.SeparatorMenuItem())

		quit_item = Gtk.MenuItem(label=_("Quit"))
		quit_item.connect("activate", lambda _item: self._on_quit())
		self._menu.append(quit_item)

		self._menu.show_all()

	def show_loading(self) -> None:
		self._header_item.set_label(_("Claude — loading…"))

	def show_usage(self, usage: UsageSnapshot) -> None:
		five_hour_pct = usage.five_hour.utilization if usage.five_hour else None

		# The systray (icon + label) shows the 5-hour usage.
		self._header_item.set_label(
			_("Claude — 5h: {percent} — {reset}").format(
				percent=format_percent(usage.five_hour),
				reset=format_reset(usage.five_hour),
			)
		)
		self._indicator.set_label(format_percent(usage.five_hour), "")

		# Everything else (overall 7 days + per-model breakdown) goes in the
		# drop-down menu. Models are whatever the API returns.
		rows = [(_("7 days"), usage.seven_day)]
		for key in _sorted_model_keys(usage.model_breakdown):
			rows.append(
				(
					_("7 days ({model})").format(model=_model_label(key)),
					usage.model_breakdown[key],
				)
			)

		for index, item in enumerate(self._detail_items):
			if index >= len(rows):
				item.set_visible(False)
				continue
			label, window = rows[index]
			if window is None or window.utilization is None:
				item.set_visible(False)
				continue
			item.set_visible(True)
			item.set_label(
				_("{label}: {percent} — {reset}").format(
					label=label,
					percent=format_weekly_pace(window),
					reset=format_reset(window),
				)
			)

		self._status_item.set_visible(False)
		self._login_item.set_visible(False)
		self._indicator.set_icon_full(self._icon_for(five_hour_pct), _("Claude usage"))

	def show_error(self, message: str, needs_login: bool = False) -> None:
		self._header_item.set_label(
			_("Claude — session expired") if needs_login else _("Claude — error")
		)
		self._status_item.set_label(message)
		self._status_item.set_visible(True)
		self._login_item.set_visible(needs_login)
		self._indicator.set_icon_full(ICON_ERROR, _("claude-usage-tray error"))

	@staticmethod
	def _icon_for(five_hour_pct: float | None) -> str:
		if five_hour_pct is None:
			return ICON_OK
		if five_hour_pct >= CRITICAL_THRESHOLD:
			return ICON_ERROR
		if five_hour_pct >= WARN_THRESHOLD:
			return ICON_WARN
		return ICON_OK


def run_main_loop() -> None:
	Gtk.main()


def quit_main_loop() -> None:
	GLib.idle_add(Gtk.main_quit)
