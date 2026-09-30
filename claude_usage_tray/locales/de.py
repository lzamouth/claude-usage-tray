"""German catalog."""

from __future__ import annotations

MESSAGES: dict[str, str] = {
	# api_client
	"Request to {url} failed: {error}": "Anfrage an {url} fehlgeschlagen: {error}",
	"Blocked by Cloudflare (HTTP {status}) — not a session problem, signing in again won't help.": (
		"Von Cloudflare blockiert (HTTP {status}) — kein Sitzungsproblem, "
		"erneutes Anmelden hilft nicht."
	),
	"claude.ai rejected the session (expired or invalid cookie) — sign in again in Firefox.": (
		"claude.ai hat die Sitzung abgelehnt (Cookie abgelaufen oder ungültig) — "
		"melde dich in Firefox erneut an."
	),
	"Unexpected response from {url}: HTTP {status}": "Unerwartete Antwort von {url}: HTTP {status}",
	"Non-JSON response from {url}": "Antwort von {url} ist kein JSON",
	"No organization found for this claude.ai account.": (
		"Keine Organisation für dieses claude.ai-Konto gefunden."
	),
	"Could not determine the organization ID.": (
		"Die Organisations-ID konnte nicht ermittelt werden."
	),
	# cookie_reader
	"Firefox profile not found: {profile}": "Firefox-Profil nicht gefunden: {profile}",
	"No Firefox profile found. Is Firefox installed and has it been started at least once?": (
		"Kein Firefox-Profil gefunden. Ist Firefox installiert und wurde es mindestens einmal gestartet?"
	),
	"cookies.sqlite not found in {path}": "cookies.sqlite nicht gefunden in {path}",
	"The claude.ai sessionKey cookie has expired — sign in to claude.ai again in Firefox.": (
		"Das sessionKey-Cookie von claude.ai ist abgelaufen — melde dich in "
		"Firefox erneut bei claude.ai an."
	),
	"sessionKey cookie not found for claude.ai — are you signed in to claude.ai in Firefox?": (
		"sessionKey-Cookie für claude.ai nicht gefunden — bist du in Firefox "
		"bei claude.ai angemeldet?"
	),
	# tray
	"unknown reset": "Reset unbekannt",
	"%m/%d %H:%M": "%d.%m. %H:%M",
	"reset {when}": "Reset {when}",
	"Mon": "Mo.",
	"Tue": "Di.",
	"Wed": "Mi.",
	"Thu": "Do.",
	"Fri": "Fr.",
	"Sat": "Sa.",
	"Sun": "So.",
	"Claude — loading…": "Claude — wird geladen…",
	"Sign in to Claude again…": "Erneut bei Claude anmelden…",
	"Refresh now": "Jetzt aktualisieren",
	"Quit": "Beenden",
	"Claude — 5h: {percent} — {reset}": "Claude — 5h: {percent} — {reset}",
	"7 days": "7 Tage",
	"7 days ({model})": "7 Tage ({model})",
	"{percent} ({used} h / {elapsed} h elapsed)": "{percent} ({used} h / {elapsed} h vergangen)",
	"{percent} ({used} d / {elapsed} d elapsed)": "{percent} ({used} Tg. / {elapsed} Tg. vergangen)",
	".": ",",
	"{label}: {percent} — {reset}": "{label}: {percent} — {reset}",
	"Updated at {time}": "Aktualisiert um {time}",
	"Last successful update: {time}": "Letzte erfolgreiche Aktualisierung: {time}",
	"Claude usage": "Claude-Nutzung",
	"Claude — session expired": "Claude — Sitzung abgelaufen",
	"Claude — error": "Claude — Fehler",
	"claude-usage-tray error": "claude-usage-tray-Fehler",
}
