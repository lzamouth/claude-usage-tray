"""French catalog."""

from __future__ import annotations

MESSAGES: dict[str, str] = {
	# api_client
	"Request to {url} failed: {error}": "Échec de la requête vers {url} : {error}",
	"Blocked by Cloudflare (HTTP {status}) — not a session problem, signing in again won't help.": (
		"Requête bloquée par Cloudflare (HTTP {status}) — ce n'est pas la "
		"session, inutile de se reconnecter."
	),
	"claude.ai rejected the session (expired or invalid cookie) — sign in again in Firefox.": (
		"Session claude.ai refusée (cookie expiré ou invalide) — "
		"reconnecte-toi dans Firefox."
	),
	"Unexpected response from {url}: HTTP {status}": "Réponse inattendue de {url} : HTTP {status}",
	"Non-JSON response from {url}": "Réponse non-JSON depuis {url}",
	"No organization found for this claude.ai account.": (
		"Aucune organisation trouvée pour ce compte claude.ai."
	),
	"Could not determine the organization ID.": (
		"Impossible de déterminer l'identifiant d'organisation."
	),
	# cookie_reader
	"Firefox profile not found: {profile}": "Profil Firefox introuvable : {profile}",
	"profiles.ini not found ({path}). Is Firefox installed and has it been started at least once?": (
		"Fichier profiles.ini introuvable ({path}). Firefox est-il installé "
		"et a-t-il déjà été lancé ?"
	),
	"No Firefox profile found in profiles.ini.": "Aucun profil Firefox trouvé dans profiles.ini.",
	"cookies.sqlite not found in {path}": "cookies.sqlite introuvable dans {path}",
	"The claude.ai sessionKey cookie has expired — sign in to claude.ai again in Firefox.": (
		"Cookie sessionKey de claude.ai expiré — reconnecte-toi à claude.ai "
		"dans Firefox."
	),
	"sessionKey cookie not found for claude.ai — are you signed in to claude.ai in Firefox?": (
		"Cookie sessionKey introuvable pour claude.ai — es-tu bien connecté à "
		"claude.ai dans Firefox ?"
	),
	# tray
	"unknown reset": "reset inconnu",
	"%m/%d %H:%M": "%d/%m %H:%M",
	"reset {when}": "reset {when}",
	"Mon": "lun.",
	"Tue": "mar.",
	"Wed": "mer.",
	"Thu": "jeu.",
	"Fri": "ven.",
	"Sat": "sam.",
	"Sun": "dim.",
	"Claude — loading…": "Claude — chargement…",
	"Sign in to Claude again…": "Se reconnecter à Claude…",
	"Refresh now": "Rafraîchir maintenant",
	"Quit": "Quitter",
	"Claude — 5h: {percent} — {reset}": "Claude — 5h : {percent} — {reset}",
	"7 days": "7 jours",
	"7 days ({model})": "7 jours ({model})",
	"{label}: {percent} — {reset}": "{label} : {percent} — {reset}",
	"Claude usage": "Utilisation Claude",
	"Claude — session expired": "Claude — session expirée",
	"Claude — error": "Claude — erreur",
	"claude-usage-tray error": "Erreur claude-usage-tray",
}
