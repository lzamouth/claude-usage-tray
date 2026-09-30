"""Systray icon and menu (StatusNotifierItem protocol via AppIndicator)."""

from __future__ import annotations

import shutil
import subprocess
from datetime import datetime

import gi

gi.require_version("Gtk", "3.0")

try:
	gi.require_version("AyatanaAppIndicator3", "0.1")
	from gi.repository import AyatanaAppIndicator3 as AppIndicator3
except (ValueError, ImportError):
	gi.require_version("AppIndicator3", "0.1")
	from gi.repository import AppIndicator3

from gi.repository import GLib, Gtk

from .api_client import FIVE_HOURS, WEEK, UsageSnapshot, UsageWindow
from .formatting import (
	format_bar,
	format_percent,
	format_reset,
	format_session_pace,
	format_weekly_pace,
	model_label,
	sorted_model_keys,
)
from .i18n import _
from .severity import Severity, snapshot_severity, window_severity

APP_ID = "claude-usage-tray"
LOGIN_URL = "https://claude.ai/login"
USAGE_URL = "https://claude.ai/settings/usage"
ICON_OK = "network-transmit-receive-symbolic"
ICON_WARN = "dialog-warning-symbolic"
ICON_ERROR = "dialog-error-symbolic"

SEVERITY_ICONS = {
	Severity.OK: ICON_OK,
	Severity.WARN: ICON_WARN,
	Severity.CRITICAL: ICON_ERROR,
}

# Prefix of menu rows whose window is close to its limit or ahead of pace.
WARNING_MARK = "⚠ "

# Menu slots reserved for the per-model breakdown — generous, so that new
# models added on claude.ai fit without touching the code.
MAX_MODEL_ROWS = 6

def open_in_firefox(url: str) -> None:
	"""Open a claude.ai page in Firefox.

	The session cookie is read from the Firefox profile, so Firefox is
	preferred explicitly; the default browser is the fallback when the
	executable cannot be found.
	"""
	firefox = shutil.which("firefox")
	command = [firefox, url] if firefox else ["xdg-open", url]
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
			Gtk.show_uri_on_window(None, url, Gtk.get_current_event_time())
		except Exception:
			pass


def open_login_page() -> None:
	open_in_firefox(LOGIN_URL)


def open_usage_page() -> None:
	open_in_firefox(USAGE_URL)


def _hidden_item(label: str = "") -> Gtk.MenuItem:
	"""Menu item that stays hidden until explicitly shown (despite show_all)."""
	item = Gtk.MenuItem(label=label)
	item.set_no_show_all(True)
	item.set_visible(False)
	return item


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

		# No item is ever made insensitive: GNOME greys those out, which made
		# the main figures hard to read. Usage rows open the usage page.
		self._header_item = Gtk.MenuItem(label=_("Claude — loading…"))
		self._header_bar_item = _hidden_item()

		# (text, bar) slots for the overall 7 days + per-model rows.
		self._detail_items: list[tuple[Gtk.MenuItem, Gtk.MenuItem]] = []
		self._status_item = _hidden_item()

		# Time of the last successful refresh; tells stale figures apart.
		self._updated_item = _hidden_item()
		self._last_success: datetime | None = None

		self._login_item = _hidden_item(_("Sign in to Claude again…"))

		self._menu = Gtk.Menu()
		self._build_static_menu()
		self._indicator.set_menu(self._menu)

	def _build_static_menu(self) -> None:
		for item in (self._header_item, self._header_bar_item):
			item.connect("activate", lambda _item: open_usage_page())
			self._menu.append(item)
		self._menu.append(Gtk.SeparatorMenuItem())

		# Slots for the details (overall 7 days + per model), filled in
		# dynamically, each a text row with its progress bar underneath.
		for _index in range(1 + MAX_MODEL_ROWS):
			pair = (Gtk.MenuItem(label=""), _hidden_item())
			for item in pair:
				item.connect("activate", lambda _item: open_usage_page())
				self._menu.append(item)
			self._detail_items.append(pair)

		self._menu.append(Gtk.SeparatorMenuItem())
		self._menu.append(self._status_item)
		self._menu.append(self._updated_item)

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
		# Only before the first figures: afterwards, keep them on screen
		# rather than flashing "loading" at every refresh.
		if self._last_success is None:
			self._header_item.set_label(_("Claude — loading…"))

	def show_usage(self, usage: UsageSnapshot) -> None:
		# The systray label shows the 5-hour usage; the icon reflects the
		# worst of all windows, pace included.
		header = _("Claude — 5h: {percent} — {reset}").format(
			percent=format_session_pace(usage.five_hour),
			reset=format_reset(usage.five_hour),
		)
		if window_severity(usage.five_hour, FIVE_HOURS) >= Severity.WARN:
			header = WARNING_MARK + header
		self._header_item.set_label(header)
		self._set_bar(self._header_bar_item, format_bar(usage.five_hour, FIVE_HOURS))
		self._indicator.set_label(format_percent(usage.five_hour), "")

		# Everything else (overall 7 days + per-model breakdown) goes in the
		# drop-down menu. Models are whatever the API returns.
		rows: list[tuple[str, UsageWindow | None]] = [(_("7 days"), usage.seven_day)]
		for key in sorted_model_keys(usage.model_breakdown):
			rows.append(
				(
					_("7 days ({model})").format(model=model_label(key)),
					usage.model_breakdown[key],
				)
			)

		for index, (item, bar_item) in enumerate(self._detail_items):
			window = rows[index][1] if index < len(rows) else None
			if window is None or window.utilization is None:
				item.set_visible(False)
				bar_item.set_visible(False)
				continue
			label = rows[index][0]
			item.set_visible(True)
			self._set_bar(bar_item, format_bar(window, WEEK))
			text = _("{label}: {percent} — {reset}").format(
				label=label,
				percent=format_weekly_pace(window),
				reset=format_reset(window),
			)
			if window_severity(window, WEEK) >= Severity.WARN:
				text = WARNING_MARK + text
			item.set_label(text)

		self._last_success = datetime.now()
		self._updated_item.set_label(
			_("Updated at {time}").format(time=self._last_success.strftime("%H:%M"))
		)
		self._updated_item.set_visible(True)
		self._status_item.set_visible(False)
		self._login_item.set_visible(False)
		self._indicator.set_icon_full(
			SEVERITY_ICONS[snapshot_severity(usage)], _("Claude usage")
		)

	def show_error(self, message: str, needs_login: bool = False) -> None:
		self._header_item.set_label(
			_("Claude — session expired") if needs_login else _("Claude — error")
		)
		self._status_item.set_label(message)
		self._status_item.set_visible(True)
		self._login_item.set_visible(needs_login)
		# The 5-hour text gave way to the error title: drop its bar too. The
		# weekly figures from the last success stay, and the timestamp below
		# tells they are not current.
		self._header_bar_item.set_visible(False)
		if self._last_success is not None:
			self._updated_item.set_label(
				_("Last successful update: {time}").format(
					time=self._last_success.strftime("%H:%M")
				)
			)
		self._indicator.set_icon_full(ICON_ERROR, _("claude-usage-tray error"))

	@staticmethod
	def _set_bar(item: Gtk.MenuItem, bar: str | None) -> None:
		item.set_visible(bar is not None)
		if bar is not None:
			item.set_label(bar)


def run_main_loop() -> None:
	Gtk.main()


def quit_main_loop() -> None:
	GLib.idle_add(Gtk.main_quit)
