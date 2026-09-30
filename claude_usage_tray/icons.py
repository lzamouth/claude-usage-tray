"""Systray gauge icon, generated as SVG.

A ring fills up with the 5-hour usage (the figure shown next to the icon);
its colour gives the overall severity (worst of all windows, pace
included); a small tick marks how much of the 5-hour window has elapsed.

Kept free of GTK so that it can be unit-tested.
"""

from __future__ import annotations

import math

from .severity import Severity

# Colours readable on both dark (GNOME) and light (KDE) panels.
SEVERITY_COLORS = {
	Severity.OK: "#4caf50",
	Severity.WARN: "#f5a623",
	Severity.CRITICAL: "#e5484d",
}
TRACK_COLOR = "#8a8a8a"
TICK_COLOR = "#f2f2f2"
TICK_OUTLINE = "#303030"

SIZE = 32
CENTER = SIZE / 2
RADIUS = 11.5
RING_WIDTH = 5.0


def _point(fraction: float, radius: float) -> tuple[float, float]:
	"""Point at ``fraction`` of a turn clockwise from 12 o'clock."""
	angle = 2 * math.pi * fraction - math.pi / 2
	return CENTER + radius * math.cos(angle), CENTER + radius * math.sin(angle)


def gauge_svg(
	utilization: float | None, elapsed: float | None, severity: Severity
) -> str:
	"""SVG of the gauge.

	``utilization`` is a percentage (None: empty ring), ``elapsed`` the share
	(0-1) of the window already gone (None: no tick).
	"""
	fraction = 0.0 if utilization is None else min(1.0, max(0.0, utilization / 100))
	circumference = 2 * math.pi * RADIUS
	parts = [
		f'<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE}" height="{SIZE}" '
		f'viewBox="0 0 {SIZE} {SIZE}">',
		f'<circle cx="{CENTER}" cy="{CENTER}" r="{RADIUS}" fill="none" '
		f'stroke="{TRACK_COLOR}" stroke-opacity="0.45" stroke-width="{RING_WIDTH}"/>',
	]
	if fraction > 0:
		# Dashed full circle, rotated so that it starts at 12 o'clock.
		parts.append(
			f'<circle cx="{CENTER}" cy="{CENTER}" r="{RADIUS}" fill="none" '
			f'stroke="{SEVERITY_COLORS[severity]}" stroke-width="{RING_WIDTH}" '
			f'stroke-dasharray="{fraction * circumference:.2f} {circumference:.2f}" '
			f'transform="rotate(-90 {CENTER} {CENTER})"/>'
		)
	if elapsed is not None:
		# Across the ring only, slightly past its edges.
		inner = _point(min(1.0, max(0.0, elapsed)), RADIUS - RING_WIDTH / 2 - 0.5)
		outer = _point(min(1.0, max(0.0, elapsed)), RADIUS + RING_WIDTH / 2 + 0.5)
		line = f'x1="{inner[0]:.2f}" y1="{inner[1]:.2f}" x2="{outer[0]:.2f}" y2="{outer[1]:.2f}"'
		# Dark outline under a light stroke: visible on any panel and fill.
		parts.append(f'<line {line} stroke="{TICK_OUTLINE}" stroke-width="3"/>')
		parts.append(f'<line {line} stroke="{TICK_COLOR}" stroke-width="1.5"/>')
	parts.append("</svg>")
	return "".join(parts)


def gauge_icon_name(
	utilization: float | None, elapsed: float | None, severity: Severity
) -> str:
	"""Icon name encoding the rendered state.

	Every state gets its own name because the panel caches icons by name.
	Values are rounded to what the ring can show at panel size.
	"""
	used = "none" if utilization is None else f"{round(min(100.0, max(0.0, utilization))):03d}"
	tick = "none" if elapsed is None else f"{round(min(1.0, max(0.0, elapsed)) * 40):02d}"
	return f"claude-usage-gauge-{used}-{tick}-{severity.name.lower()}"
