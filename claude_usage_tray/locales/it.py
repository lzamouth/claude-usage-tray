"""Italian catalog."""

from __future__ import annotations

MESSAGES: dict[str, str] = {
	# api_client
	"Request to {url} failed: {error}": "Richiesta a {url} non riuscita: {error}",
	"Blocked by Cloudflare (HTTP {status}) — not a session problem, signing in again won't help.": (
		"Bloccato da Cloudflare (HTTP {status}) — non è un problema di "
		"sessione, accedere di nuovo non servirà."
	),
	"claude.ai rejected the session (expired or invalid cookie) — sign in again in Firefox.": (
		"claude.ai ha rifiutato la sessione (cookie scaduto o non valido) — "
		"accedi di nuovo in Firefox."
	),
	"Unexpected response from {url}: HTTP {status}": "Risposta inattesa da {url}: HTTP {status}",
	"Non-JSON response from {url}": "Risposta non JSON da {url}",
	"No organization found for this claude.ai account.": (
		"Nessuna organizzazione trovata per questo account claude.ai."
	),
	"Could not determine the organization ID.": (
		"Impossibile determinare l'ID dell'organizzazione."
	),
	# cookie_reader
	"Firefox profile not found: {profile}": "Profilo Firefox non trovato: {profile}",
	"No Firefox profile found. Is Firefox installed and has it been started at least once?": (
		"Nessun profilo Firefox trovato. Firefox è installato ed è stato avviato almeno una volta?"
	),
	"cookies.sqlite not found in {path}": "cookies.sqlite non trovato in {path}",
	"The claude.ai sessionKey cookie has expired — sign in to claude.ai again in Firefox.": (
		"Il cookie sessionKey di claude.ai è scaduto — accedi di nuovo a "
		"claude.ai in Firefox."
	),
	"sessionKey cookie not found for claude.ai — are you signed in to claude.ai in Firefox?": (
		"Cookie sessionKey di claude.ai non trovato — hai effettuato l'accesso "
		"a claude.ai in Firefox?"
	),
	# tray
	"unknown reset": "reset sconosciuto",
	"reset in {remaining} ({when})": "reset tra {remaining} ({when})",
	"{minutes} min": "{minutes} min",
	"{hours}h {minutes:02d}m": "{hours} h {minutes:02d} min",
	"{days}d {hours}h": "{days} g {hours} h",
	"Mon": "lun",
	"Tue": "mar",
	"Wed": "mer",
	"Thu": "gio",
	"Fri": "ven",
	"Sat": "sab",
	"Sun": "dom",
	"Claude — loading…": "Claude — caricamento…",
	"Sign in to Claude again…": "Accedi di nuovo a Claude…",
	"Refresh now": "Aggiorna ora",
	"Quit": "Esci",
	"Claude — 5h: {percent} — {reset}": "Claude — 5h: {percent} — {reset}",
	"7 days": "7 giorni",
	"7 days ({model})": "7 giorni ({model})",
	"{percent} ({used} h / {elapsed} h elapsed)": "{percent} ({used} h / {elapsed} h trascorse)",
	"{percent} ({used} d / {elapsed} d elapsed)": "{percent} ({used} g / {elapsed} g trascorsi)",
	".": ",",
	"{label}: {percent} — {reset}": "{label}: {percent} — {reset}",
	"Updated at {time}": "Aggiornato alle {time}",
	"Last successful update: {time}": "Ultimo aggiornamento riuscito: {time}",
	"Claude usage": "Utilizzo di Claude",
	"Claude — session expired": "Claude — sessione scaduta",
	"Claude — error": "Claude — errore",
	"claude-usage-tray error": "Errore di claude-usage-tray",
	# notifications
	"5 hours": "5 h",
	"Claude: {window} limit at {percent}": "Claude: limite {window} al {percent}",
	"Claude: {window} limit reset": "Claude: limite {window} azzerato",
	"Usage is available again.": "L'utilizzo è di nuovo disponibile.",
}
