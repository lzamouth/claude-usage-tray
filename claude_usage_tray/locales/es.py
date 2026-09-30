"""Spanish catalog."""

from __future__ import annotations

MESSAGES: dict[str, str] = {
	# api_client
	"Request to {url} failed: {error}": "Error en la solicitud a {url}: {error}",
	"Blocked by Cloudflare (HTTP {status}) — not a session problem, signing in again won't help.": (
		"Bloqueado por Cloudflare (HTTP {status}) — no es un problema de "
		"sesión, volver a iniciar sesión no servirá de nada."
	),
	"claude.ai rejected the session (expired or invalid cookie) — sign in again in Firefox.": (
		"claude.ai rechazó la sesión (cookie caducada o no válida) — vuelve a "
		"iniciar sesión en Firefox."
	),
	"Unexpected response from {url}: HTTP {status}": "Respuesta inesperada de {url}: HTTP {status}",
	"Non-JSON response from {url}": "Respuesta no JSON de {url}",
	"No organization found for this claude.ai account.": (
		"No se encontró ninguna organización para esta cuenta de claude.ai."
	),
	"Could not determine the organization ID.": (
		"No se pudo determinar el ID de la organización."
	),
	# cookie_reader
	"Firefox profile not found: {profile}": "No se encontró el perfil de Firefox: {profile}",
	"profiles.ini not found ({path}). Is Firefox installed and has it been started at least once?": (
		"No se encontró profiles.ini ({path}). ¿Está Firefox instalado y se "
		"ha iniciado al menos una vez?"
	),
	"No Firefox profile found in profiles.ini.": "No se encontró ningún perfil de Firefox en profiles.ini.",
	"cookies.sqlite not found in {path}": "No se encontró cookies.sqlite en {path}",
	"The claude.ai sessionKey cookie has expired — sign in to claude.ai again in Firefox.": (
		"La cookie sessionKey de claude.ai ha caducado — vuelve a iniciar "
		"sesión en claude.ai en Firefox."
	),
	"sessionKey cookie not found for claude.ai — are you signed in to claude.ai in Firefox?": (
		"No se encontró la cookie sessionKey de claude.ai — ¿has iniciado "
		"sesión en claude.ai en Firefox?"
	),
	# tray
	"unknown reset": "reinicio desconocido",
	"%m/%d %H:%M": "%d/%m %H:%M",
	"reset {when}": "reinicio {when}",
	"Mon": "lun.",
	"Tue": "mar.",
	"Wed": "mié.",
	"Thu": "jue.",
	"Fri": "vie.",
	"Sat": "sáb.",
	"Sun": "dom.",
	"Claude — loading…": "Claude — cargando…",
	"Sign in to Claude again…": "Volver a iniciar sesión en Claude…",
	"Refresh now": "Actualizar ahora",
	"Quit": "Salir",
	"Claude — 5h: {percent} — {reset}": "Claude — 5h: {percent} — {reset}",
	"7 days": "7 días",
	"7 days ({model})": "7 días ({model})",
	"{percent} ({used} h / {elapsed} h elapsed)": "{percent} ({used} h / {elapsed} h transcurridas)",
	"{percent} ({used} d / {elapsed} d elapsed)": "{percent} ({used} d / {elapsed} d transcurridos)",
	".": ",",
	"{label}: {percent} — {reset}": "{label}: {percent} — {reset}",
	"Claude usage": "Uso de Claude",
	"Claude — session expired": "Claude — sesión caducada",
	"Claude — error": "Claude — error",
	"claude-usage-tray error": "Error de claude-usage-tray",
}
