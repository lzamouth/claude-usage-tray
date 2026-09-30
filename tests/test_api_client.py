"""API response parsing and error classification tests (no network)."""

from __future__ import annotations

import unittest
from unittest import mock

import requests

from claude_usage_tray import api_client
from claude_usage_tray.cookie_reader import expiry_seconds


def _response(status: int, headers: dict[str, str], body: bytes = b"{}") -> requests.Response:
	response = requests.Response()
	response.status_code = status
	response.headers.update(headers)
	response._content = body
	return response


class SnapshotParsingTest(unittest.TestCase):
	def test_current_schema(self) -> None:
		data = {
			"five_hour": {"utilization": 3.0, "resets_at": "2026-09-30T19:40:00+00:00"},
			"seven_day": {"utilization": 16.0, "resets_at": "2026-10-06T08:00:00Z"},
			"seven_day_opus": None,
			"seven_day_breakdown": {"rows": [{"key": "chat", "percent": 1}]},
			"limits": [
				{"kind": "session", "percent": 3, "scope": None},
				{
					"kind": "weekly_scoped",
					"percent": 10,
					"resets_at": "2026-10-06T07:59:59+00:00",
					"scope": {"model": {"id": None, "display_name": "Fable"}},
				},
			],
		}
		snapshot = api_client.UsageSnapshot.from_dict(data)
		self.assertEqual(3.0, snapshot.five_hour.utilization)
		self.assertEqual(16.0, snapshot.seven_day.utilization)
		self.assertEqual({"fable"}, snapshot.model_breakdown.keys())
		self.assertEqual(10, snapshot.model_breakdown["fable"].utilization)

	def test_legacy_schema(self) -> None:
		data = {
			"five_hour": None,
			"seven_day_sonnet": {"utilization": 42.0, "resets_at": None},
			"seven_day_oauth_apps": {"utilization": 1.0, "resets_at": None},
		}
		snapshot = api_client.UsageSnapshot.from_dict(data)
		self.assertIsNone(snapshot.five_hour)
		self.assertEqual({"sonnet"}, snapshot.model_breakdown.keys())


class ErrorClassificationTest(unittest.TestCase):
	def _raised(self, response: requests.Response) -> type[Exception] | None:
		client = api_client.ClaudeUsageClient("dummy")
		with mock.patch.object(client._session, "get", return_value=response):
			try:
				client._get("/organizations")
			except api_client.ApiError as exc:
				return type(exc)
		return None

	def test_classification(self) -> None:
		cases = [
			(_response(403, {"cf-mitigated": "challenge", "content-type": "text/html"}), api_client.BlockedError),
			(_response(403, {"content-type": "text/html"}), api_client.BlockedError),
			(_response(403, {"content-type": "application/json"}), api_client.AuthError),
			(_response(401, {"content-type": "application/json"}), api_client.AuthError),
			(_response(500, {}), api_client.ApiError),
			(_response(200, {"content-type": "application/json"}, b"[]"), None),
		]
		for response, expected in cases:
			with self.subTest(status=response.status_code, headers=dict(response.headers)):
				self.assertIs(expected, self._raised(response))

	def test_browser_headers_sent(self) -> None:
		headers = api_client.ClaudeUsageClient("dummy")._session.headers
		self.assertEqual("cors", headers["Sec-Fetch-Mode"])
		self.assertEqual("same-origin", headers["Sec-Fetch-Site"])


class CookieExpiryTest(unittest.TestCase):
	def test_expiry_units(self) -> None:
		self.assertIsNone(expiry_seconds(0))
		self.assertEqual(1_790_000_000.0, expiry_seconds(1_790_000_000))
		self.assertEqual(1_790_000_000.0, expiry_seconds(1_790_000_000_000))


if __name__ == "__main__":
	unittest.main()
