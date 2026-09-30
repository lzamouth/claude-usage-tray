"""System events that call for an immediate refresh: resume and network up.

Without them, figures stay stale after a suspend: the worker's timer runs on
the monotonic clock, which does not advance while the machine sleeps.

Callbacks run in the GLib main loop (main thread).
"""

from __future__ import annotations

from collections.abc import Callable

from gi.repository import Gio, GLib

LOGIND_BUS_NAME = "org.freedesktop.login1"
LOGIND_PATH = "/org/freedesktop/login1"
LOGIND_INTERFACE = "org.freedesktop.login1.Manager"


class SystemEventWatcher:
	"""Calls ``on_wake`` after a resume from suspend or when the network returns."""

	def __init__(self, on_wake: Callable[[], None]) -> None:
		self._on_wake = on_wake
		self._network_monitor = Gio.NetworkMonitor.get_default()
		self._network_available = self._network_monitor.get_network_available()
		self._network_monitor.connect("network-changed", self._on_network_changed)
		self._watch_suspend()

	def _watch_suspend(self) -> None:
		try:
			bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
		except GLib.Error:
			# No system bus (container, unusual setup): resume refresh is lost,
			# the regular polling still works.
			return
		bus.signal_subscribe(
			LOGIND_BUS_NAME,
			LOGIND_INTERFACE,
			"PrepareForSleep",
			LOGIND_PATH,
			None,
			Gio.DBusSignalFlags.NONE,
			self._on_prepare_for_sleep,
		)

	def _on_prepare_for_sleep(self, _conn, _sender, _path, _iface, _signal, params) -> None:
		# PrepareForSleep(true) before suspending, (false) after resuming.
		(going_to_sleep,) = params.unpack()
		if not going_to_sleep:
			self._on_wake()

	def _on_network_changed(self, _monitor, available: bool) -> None:
		# The signal fires on every interface change; only react to the
		# offline → online transition.
		if available and not self._network_available:
			self._on_wake()
		self._network_available = available
