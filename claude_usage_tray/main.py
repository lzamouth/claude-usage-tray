"""Entry point: refresh loop + systray icon."""

from __future__ import annotations

import signal
import threading
import time

from .api_client import ApiError, AuthError, ClaudeUsageClient
from .config import load_config
from .cookie_reader import CookieError, read_session_key
from .i18n import set_language
from .tray import UsageTray, open_login_page, quit_main_loop, run_main_loop

from gi.repository import GLib

# After a click on "Sign in to Claude again…", poll quickly to pick up the new
# session as soon as the user has signed in.
FAST_RETRY_INTERVAL_SECONDS = 10
FAST_RETRY_WINDOW_SECONDS = 300

# On repeated failures the interval doubles after each failure (capped), so
# as not to make a Cloudflare block or rate limit worse.
MAX_BACKOFF_SECONDS = 3600


class RefreshWorker:
	"""Polls claude.ai in the background and pushes results to the UI.

	Runs in a daemon thread; every UI update goes through GLib.idle_add so
	that GTK is only ever touched from the main thread.
	"""

	def __init__(self, tray: UsageTray, poll_interval: int, firefox_profile: str | None) -> None:
		self._tray = tray
		self._poll_interval = poll_interval
		self._firefox_profile = firefox_profile

		self._stop_event = threading.Event()
		self._refresh_event = threading.Event()
		self._cached_org_id: str | None = None
		# Monotonic timestamp at which the fast polling window ends.
		self._fast_retry_until = 0.0
		# Consecutive failures, reset on the first success.
		self._consecutive_failures = 0

		self._thread = threading.Thread(target=self._run, daemon=True)

	def start(self) -> None:
		self._thread.start()

	def stop(self) -> None:
		self._stop_event.set()
		self._refresh_event.set()

	def request_refresh(self) -> None:
		self._refresh_event.set()

	def start_fast_retry(self) -> None:
		"""Poll frequently for a few minutes (after a sign-in)."""
		self._fast_retry_until = time.monotonic() + FAST_RETRY_WINDOW_SECONDS
		self._refresh_event.set()

	def _next_delay(self) -> float:
		if time.monotonic() < self._fast_retry_until:
			return min(FAST_RETRY_INTERVAL_SECONDS, self._poll_interval)
		if self._consecutive_failures == 0:
			return self._poll_interval
		backoff = self._poll_interval * 2 ** min(self._consecutive_failures - 1, 10)
		return max(self._poll_interval, min(backoff, MAX_BACKOFF_SECONDS))

	def _run(self) -> None:
		while not self._stop_event.is_set():
			self._refresh_once()
			self._refresh_event.clear()
			self._refresh_event.wait(timeout=self._next_delay())

	def _refresh_once(self) -> None:
		GLib.idle_add(self._tray.show_loading)
		try:
			session_key = read_session_key(self._firefox_profile)
			client = ClaudeUsageClient(session_key)

			if self._cached_org_id is None:
				self._cached_org_id = client.get_default_organization_id()

			usage = client.get_usage(self._cached_org_id)
		except CookieError as exc:
			# Missing/unreadable cookie: signing in again in Firefox is the fix.
			self._consecutive_failures += 1
			GLib.idle_add(self._tray.show_error, str(exc), True)
		except AuthError as exc:
			self._consecutive_failures += 1
			self._cached_org_id = None
			GLib.idle_add(self._tray.show_error, str(exc), True)
		except ApiError as exc:
			# Includes BlockedError (Cloudflare): signing in would not help.
			self._consecutive_failures += 1
			GLib.idle_add(self._tray.show_error, str(exc), False)
		else:
			# Valid session: no more fast polling or backoff needed.
			self._consecutive_failures = 0
			self._fast_retry_until = 0.0
			GLib.idle_add(self._tray.show_usage, usage)


def main() -> None:
	config = load_config()
	# Must run before the UI is built. Strings are translated when used,
	# never at import time, so module imports above are unaffected.
	set_language(config.language)

	worker_holder: dict[str, RefreshWorker] = {}

	def on_refresh_requested() -> None:
		worker_holder["worker"].request_refresh()

	def on_quit() -> None:
		worker_holder["worker"].stop()
		quit_main_loop()

	def on_login_requested() -> None:
		open_login_page()
		# Fast polling: the new session is picked up as soon as the cookie
		# lands in the Firefox profile, without any further click.
		worker_holder["worker"].start_fast_retry()

	tray = UsageTray(
		on_refresh_requested=on_refresh_requested,
		on_quit=on_quit,
		on_login_requested=on_login_requested,
	)

	worker = RefreshWorker(
		tray=tray,
		poll_interval=config.poll_interval_seconds,
		firefox_profile=config.firefox_profile,
	)
	worker_holder["worker"] = worker
	worker.start()

	# Lets Ctrl+C work even under the GTK main loop.
	signal.signal(signal.SIGINT, lambda *_args: on_quit())
	signal.signal(signal.SIGTERM, lambda *_args: on_quit())

	run_main_loop()


if __name__ == "__main__":
	main()
