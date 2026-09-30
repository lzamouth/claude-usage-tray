"""Dutch catalog (standard Dutch, also used for nl_BE)."""

from __future__ import annotations

MESSAGES: dict[str, str] = {
	# api_client
	"Request to {url} failed: {error}": "Verzoek aan {url} mislukt: {error}",
	"Blocked by Cloudflare (HTTP {status}) — not a session problem, signing in again won't help.": (
		"Geblokkeerd door Cloudflare (HTTP {status}) — geen sessieprobleem, "
		"opnieuw inloggen helpt niet."
	),
	"claude.ai rejected the session (expired or invalid cookie) — sign in again in Firefox.": (
		"claude.ai heeft de sessie geweigerd (cookie verlopen of ongeldig) — "
		"log opnieuw in via Firefox."
	),
	"Unexpected response from {url}: HTTP {status}": "Onverwacht antwoord van {url}: HTTP {status}",
	"Non-JSON response from {url}": "Antwoord van {url} is geen JSON",
	"No organization found for this claude.ai account.": (
		"Geen organisatie gevonden voor dit claude.ai-account."
	),
	"Could not determine the organization ID.": (
		"Kan de organisatie-ID niet bepalen."
	),
	# cookie_reader
	"Firefox profile not found: {profile}": "Firefox-profiel niet gevonden: {profile}",
	"No Firefox profile found. Is Firefox installed and has it been started at least once?": (
		"Geen Firefox-profiel gevonden. Is Firefox geïnstalleerd en al minstens één keer gestart?"
	),
	"cookies.sqlite not found in {path}": "cookies.sqlite niet gevonden in {path}",
	"The claude.ai sessionKey cookie has expired — sign in to claude.ai again in Firefox.": (
		"De sessionKey-cookie van claude.ai is verlopen — log opnieuw in op "
		"claude.ai via Firefox."
	),
	"sessionKey cookie not found for claude.ai — are you signed in to claude.ai in Firefox?": (
		"sessionKey-cookie voor claude.ai niet gevonden — ben je in Firefox "
		"ingelogd op claude.ai?"
	),
	# tray
	"unknown reset": "reset onbekend",
	"%m/%d %H:%M": "%d-%m %H:%M",
	"reset {when}": "reset {when}",
	"Mon": "ma",
	"Tue": "di",
	"Wed": "wo",
	"Thu": "do",
	"Fri": "vr",
	"Sat": "za",
	"Sun": "zo",
	"Claude — loading…": "Claude — laden…",
	"Sign in to Claude again…": "Opnieuw inloggen bij Claude…",
	"Refresh now": "Nu vernieuwen",
	"Quit": "Afsluiten",
	"Claude — 5h: {percent} — {reset}": "Claude — 5h: {percent} — {reset}",
	"7 days": "7 dagen",
	"7 days ({model})": "7 dagen ({model})",
	"{percent} ({used} h / {elapsed} h elapsed)": "{percent} ({used} u / {elapsed} u verstreken)",
	"{percent} ({used} d / {elapsed} d elapsed)": "{percent} ({used} d / {elapsed} d verstreken)",
	".": ",",
	"{label}: {percent} — {reset}": "{label}: {percent} — {reset}",
	"Updated at {time}": "Bijgewerkt om {time}",
	"Last successful update: {time}": "Laatste geslaagde update: {time}",
	"Claude usage": "Claude-gebruik",
	"Claude — session expired": "Claude — sessie verlopen",
	"Claude — error": "Claude — fout",
	"claude-usage-tray error": "claude-usage-tray-fout",
}
