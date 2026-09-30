"""Gauge icon tests: well-formed SVG, one stable name per rendered state."""

from __future__ import annotations

import unittest
import xml.etree.ElementTree as ElementTree

from claude_usage_tray.icons import SEVERITY_COLORS, gauge_icon_name, gauge_svg
from claude_usage_tray.severity import Severity

SVG = "{http://www.w3.org/2000/svg}"


class GaugeSvgTest(unittest.TestCase):
	def parse(self, svg: str) -> ElementTree.Element:
		return ElementTree.fromstring(svg)

	def test_arc_and_tick(self) -> None:
		root = self.parse(gauge_svg(40.0, 0.5, Severity.WARN))
		circles = root.findall(f"{SVG}circle")
		self.assertEqual(2, len(circles))  # track + arc
		self.assertEqual(SEVERITY_COLORS[Severity.WARN], circles[1].get("stroke"))
		self.assertEqual(2, len(root.findall(f"{SVG}line")))  # tick outline + tick

	def test_empty_gauge(self) -> None:
		root = self.parse(gauge_svg(None, None, Severity.OK))
		self.assertEqual(1, len(root.findall(f"{SVG}circle")))  # track only
		self.assertEqual([], root.findall(f"{SVG}line"))
		self.assertEqual(1, len(self.parse(gauge_svg(0.0, None, Severity.OK)).findall(f"{SVG}circle")))

	def test_overflow_is_clamped(self) -> None:
		full = self.parse(gauge_svg(150.0, 1.4, Severity.CRITICAL))
		dash = full.findall(f"{SVG}circle")[1].get("stroke-dasharray").split()
		self.assertEqual(dash[0], dash[1])  # arc length == circumference


class GaugeNameTest(unittest.TestCase):
	def test_names(self) -> None:
		self.assertEqual(
			"claude-usage-gauge-042-20-warn", gauge_icon_name(42.2, 0.5, Severity.WARN)
		)
		self.assertEqual(
			"claude-usage-gauge-none-none-ok", gauge_icon_name(None, None, Severity.OK)
		)
		# Differences the ring cannot show share a name (and a file).
		self.assertEqual(
			gauge_icon_name(42.2, 0.501, Severity.OK), gauge_icon_name(41.8, 0.499, Severity.OK)
		)


if __name__ == "__main__":
	unittest.main()
