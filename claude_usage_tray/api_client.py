"""Client for the internal (unofficial) claude.ai API.

This API is not publicly documented: it may change or be blocked without
notice. Endpoints used:

	GET https://claude.ai/api/organizations
	GET https://claude.ai/api/organizations/{org_id}/usage
"""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any

import requests

from .i18n import _, current_language

BASE_URL = "https://claude.ai/api"
# Used when the installed Firefox version cannot be read.
FALLBACK_FIREFOX_VERSION = "140"
TIMEOUT_SECONDS = 15

# Window lengths: the "five_hour" session, and the weekly windows (overall
# "seven_day" and per-model limits).
FIVE_HOURS = timedelta(hours=5)
WEEK = timedelta(days=7)


class ApiError(RuntimeError):
	"""Generic claude.ai API call failure."""


class AuthError(ApiError):
	"""The session cookie is invalid, expired or missing (401/403)."""


class BlockedError(ApiError):
	"""Request blocked by Cloudflare (anti-bot challenge), not by the session.

	Signing in again in Firefox does not help, so the UI must not offer the
	sign-in button in this case.
	"""


@lru_cache(maxsize=1)
def firefox_user_agent() -> str:
	"""User-Agent matching the installed Firefox version (read once)."""
	version = FALLBACK_FIREFOX_VERSION
	firefox = shutil.which("firefox")
	if firefox:
		try:
			output = subprocess.run(
				[firefox, "--version"],
				capture_output=True,
				text=True,
				timeout=10,
			).stdout
		except (OSError, subprocess.SubprocessError):
			output = ""
		match = re.search(r"Firefox (\d+)\.", output)
		if match:
			version = match.group(1)
	return (
		f"Mozilla/5.0 (X11; Linux x86_64; rv:{version}.0) "
		f"Gecko/20100101 Firefox/{version}.0"
	)


def _accept_language() -> str:
	"""Accept-Language header for the active UI language."""
	language = current_language()
	if language == "en":
		return "en-US,en;q=0.5"
	return f"{language},en-US;q=0.7,en;q=0.3"


def is_cloudflare_block(response: requests.Response) -> bool:
	"""True if the response is a Cloudflare challenge rather than an API reply."""
	if "cf-mitigated" in response.headers:
		return True
	content_type = response.headers.get("content-type", "")
	return response.status_code == 403 and content_type.startswith("text/html")


def _parse_datetime(raw: str | None) -> datetime | None:
	if not raw:
		return None
	try:
		return datetime.fromisoformat(raw.replace("Z", "+00:00"))
	except ValueError:
		return None


@dataclass(frozen=True)
class UsageWindow:
	utilization: float | None
	resets_at: datetime | None

	@classmethod
	def from_dict(cls, data: dict[str, Any] | None) -> "UsageWindow | None":
		if not data:
			return None
		return cls(
			utilization=data.get("utilization"),
			resets_at=_parse_datetime(data.get("resets_at")),
		)

	def elapsed_fraction(self, period: timedelta, now: datetime | None = None) -> float | None:
		"""Share of the window already elapsed (0-1), or None without a reset time.

		The window is assumed to start ``period`` before ``resets_at``.
		"""
		if self.resets_at is None:
			return None
		now = now or datetime.now(timezone.utc)
		remaining = (self.resets_at - now) / period
		return min(1.0, max(0.0, 1.0 - remaining))


# "seven_day_*" keys that do not name a model (no per-model row for them).
NON_MODEL_SEVEN_DAY_SUFFIXES = {"oauth_apps", "cowork"}


@dataclass(frozen=True)
class UsageSnapshot:
	five_hour: UsageWindow | None
	seven_day: UsageWindow | None
	# Per-model breakdown (sonnet, opus, fable, ...), extracted dynamically
	# from the response so that new models show up without code changes.
	model_breakdown: dict[str, UsageWindow]

	@classmethod
	def from_dict(cls, data: dict[str, Any]) -> "UsageSnapshot":
		breakdown: dict[str, UsageWindow] = {}

		# Legacy schema: "seven_day_<model>" fields.
		for key, value in data.items():
			if not key.startswith("seven_day_") or key == "seven_day":
				continue
			suffix = key[len("seven_day_") :]
			if suffix in NON_MODEL_SEVEN_DAY_SUFFIXES:
				continue
			# Skip anything that is not a usage window (e.g.
			# "seven_day_breakdown", which is a per-surface split).
			if not isinstance(value, dict) or "utilization" not in value:
				continue
			window = UsageWindow.from_dict(value)
			if window is not None:
				breakdown[suffix] = window

		# Current schema: per-model weekly limits live in "limits"
		# (kind "weekly_scoped", model in scope.model.display_name).
		for limit in data.get("limits") or []:
			if not isinstance(limit, dict) or limit.get("kind") != "weekly_scoped":
				continue
			model = ((limit.get("scope") or {}).get("model") or {}).get("display_name")
			if not model:
				continue
			breakdown[model.lower().replace(" ", "_")] = UsageWindow(
				utilization=limit.get("percent"),
				resets_at=_parse_datetime(limit.get("resets_at")),
			)

		return cls(
			five_hour=UsageWindow.from_dict(data.get("five_hour")),
			seven_day=UsageWindow.from_dict(data.get("seven_day")),
			model_breakdown=breakdown,
		)


class ClaudeUsageClient:
	"""Small HTTP client for the internal claude.ai API."""

	def __init__(self, session_key: str) -> None:
		self._session = requests.Session()
		# The Sec-Fetch-* headers are essential: without them Cloudflare
		# answers with a challenge (403 + cf-mitigated), whatever the UA.
		self._session.headers.update(
			{
				"User-Agent": firefox_user_agent(),
				"Accept": "application/json",
				"Accept-Language": _accept_language(),
				"Referer": "https://claude.ai/",
				"Origin": "https://claude.ai",
				"Sec-Fetch-Site": "same-origin",
				"Sec-Fetch-Mode": "cors",
				"Sec-Fetch-Dest": "empty",
			}
		)
		self._session.cookies.set("sessionKey", session_key, domain="claude.ai")

	def _get(self, path: str) -> Any:
		url = f"{BASE_URL}{path}"
		try:
			response = self._session.get(url, timeout=TIMEOUT_SECONDS)
		except requests.RequestException as exc:
			raise ApiError(
				_("Request to {url} failed: {error}").format(url=url, error=exc)
			) from exc

		if is_cloudflare_block(response):
			raise BlockedError(
				_(
					"Blocked by Cloudflare (HTTP {status}) — not a session "
					"problem, signing in again won't help."
				).format(status=response.status_code)
			)
		if response.status_code in (401, 403):
			raise AuthError(
				_(
					"claude.ai rejected the session (expired or invalid "
					"cookie) — sign in again in Firefox."
				)
			)
		if not response.ok:
			raise ApiError(
				_("Unexpected response from {url}: HTTP {status}").format(
					url=url, status=response.status_code
				)
			)

		try:
			return response.json()
		except ValueError as exc:
			raise ApiError(_("Non-JSON response from {url}").format(url=url)) from exc

	def get_default_organization_id(self) -> str:
		orgs = self._get("/organizations")
		if not isinstance(orgs, list) or not orgs:
			raise ApiError(_("No organization found for this claude.ai account."))
		org_id = orgs[0].get("uuid")
		if not org_id:
			raise ApiError(_("Could not determine the organization ID."))
		return org_id

	def get_usage(self, org_id: str) -> UsageSnapshot:
		data = self._get(f"/organizations/{org_id}/usage")
		return UsageSnapshot.from_dict(data)
