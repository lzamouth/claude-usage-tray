#!/usr/bin/env python3
"""claude-usage-tray diagnostics: find out exactly where things break.

Prints the Firefox profile in use, every sessionKey cookie row (expiry,
container), then calls the API with bare headers and with the applet's own
client, showing HTTP status and Cloudflare headers.

Usage:
	./.venv/bin/python diag_usage.py
"""

from __future__ import annotations

import datetime as dt
import sqlite3
import sys
import tempfile
from pathlib import Path

import requests

from claude_usage_tray.api_client import ApiError, ClaudeUsageClient, firefox_user_agent
from claude_usage_tray.cookie_reader import (
	COOKIE_HOSTS,
	COOKIE_NAME,
	copy_cookie_db,
	expiry_seconds,
	find_profile,
	read_session_key,
)

BASE_URL = "https://claude.ai/api"


def section(title: str) -> None:
	print(f"\n=== {title} ===")


def show_cookie_rows(profile: Path) -> None:
	"""List every sessionKey row, to spot containers or expired cookies."""
	with tempfile.TemporaryDirectory() as tmp:
		db_path = copy_cookie_db(profile, Path(tmp))
		conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
		placeholders = ",".join("?" for _host in COOKIE_HOSTS)
		rows = conn.execute(
			f"SELECT host, expiry, length(value), originAttributes FROM moz_cookies "
			f"WHERE name = ? AND host IN ({placeholders})",
			(COOKIE_NAME, *COOKIE_HOSTS),
		).fetchall()
		conn.close()

	print(f"{len(rows)} sessionKey cookie row(s):")
	now = dt.datetime.now(dt.timezone.utc)
	for host, expiry, length, origin_attrs in rows:
		seconds = expiry_seconds(expiry)
		expires = dt.datetime.fromtimestamp(seconds, dt.timezone.utc) if seconds else None
		state = "EXPIRED" if expires and expires < now else "valid"
		print(
			f"  host={host} len={length} expiry={expires} ({state}) "
			f"originAttributes={origin_attrs!r}"
		)


def bare_request(key: str) -> None:
	"""Call /organizations without Sec-Fetch-* headers (expected: Cloudflare 403)."""
	session = requests.Session()
	session.headers.update(
		{
			"User-Agent": firefox_user_agent(),
			"Accept": "application/json",
			"Referer": "https://claude.ai/",
		}
	)
	session.cookies.set("sessionKey", key, domain="claude.ai")
	try:
		response = session.get(f"{BASE_URL}/organizations", timeout=20)
	except requests.RequestException as exc:
		print(f"EXCEPTION: {exc}")
		return
	print(f"HTTP {response.status_code}")
	for header in ("cf-ray", "cf-mitigated", "server", "content-type"):
		if header in response.headers:
			print(f"    {header}: {response.headers[header]}")


def applet_request(key: str) -> None:
	"""Fetch usage exactly as the applet does."""
	client = ClaudeUsageClient(key)
	try:
		usage = client.get_usage(client.get_default_organization_id())
	except ApiError as exc:
		print(f"ERROR {type(exc).__name__}: {exc}")
		return
	print("5 hours:", usage.five_hour)
	print("7 days :", usage.seven_day)
	print("models :", usage.model_breakdown)


def main() -> int:
	section("Firefox profile")
	try:
		profile = find_profile(None)
	except Exception as exc:
		print("ERROR:", exc)
		return 1
	print("profile:", profile)
	print("UA     :", firefox_user_agent())

	section("sessionKey cookie")
	try:
		key = read_session_key(None)
	except Exception as exc:
		print("ERROR:", exc)
		return 1
	print("length:", len(key))
	print("prefix:", key[:12] + "…")
	show_cookie_rows(profile)

	section("Bare request (no Sec-Fetch-* headers)")
	bare_request(key)

	section("Applet client (ClaudeUsageClient)")
	applet_request(key)
	return 0


if __name__ == "__main__":
	sys.exit(main())
