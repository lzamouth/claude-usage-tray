"""Portuguese catalog (Brazilian Portuguese, also used for pt_PT)."""

from __future__ import annotations

MESSAGES: dict[str, str] = {
	# api_client
	"Request to {url} failed: {error}": "Falha na requisição para {url}: {error}",
	"Blocked by Cloudflare (HTTP {status}) — not a session problem, signing in again won't help.": (
		"Bloqueado pelo Cloudflare (HTTP {status}) — não é um problema de "
		"sessão, fazer login novamente não vai adiantar."
	),
	"claude.ai rejected the session (expired or invalid cookie) — sign in again in Firefox.": (
		"O claude.ai recusou a sessão (cookie expirado ou inválido) — faça "
		"login novamente no Firefox."
	),
	"Unexpected response from {url}: HTTP {status}": "Resposta inesperada de {url}: HTTP {status}",
	"Non-JSON response from {url}": "Resposta não JSON de {url}",
	"No organization found for this claude.ai account.": (
		"Nenhuma organização encontrada para esta conta do claude.ai."
	),
	"Could not determine the organization ID.": (
		"Não foi possível determinar o ID da organização."
	),
	# cookie_reader
	"Firefox profile not found: {profile}": "Perfil do Firefox não encontrado: {profile}",
	"profiles.ini not found ({path}). Is Firefox installed and has it been started at least once?": (
		"profiles.ini não encontrado ({path}). O Firefox está instalado e já "
		"foi aberto pelo menos uma vez?"
	),
	"No Firefox profile found in profiles.ini.": "Nenhum perfil do Firefox encontrado em profiles.ini.",
	"cookies.sqlite not found in {path}": "cookies.sqlite não encontrado em {path}",
	"The claude.ai sessionKey cookie has expired — sign in to claude.ai again in Firefox.": (
		"O cookie sessionKey do claude.ai expirou — faça login novamente no "
		"claude.ai pelo Firefox."
	),
	"sessionKey cookie not found for claude.ai — are you signed in to claude.ai in Firefox?": (
		"Cookie sessionKey do claude.ai não encontrado — você está conectado "
		"ao claude.ai no Firefox?"
	),
	# tray
	"unknown reset": "reinício desconhecido",
	"%m/%d %H:%M": "%d/%m %H:%M",
	"reset {when}": "reinício {when}",
	"Mon": "seg.",
	"Tue": "ter.",
	"Wed": "qua.",
	"Thu": "qui.",
	"Fri": "sex.",
	"Sat": "sáb.",
	"Sun": "dom.",
	"Claude — loading…": "Claude — carregando…",
	"Sign in to Claude again…": "Fazer login novamente no Claude…",
	"Refresh now": "Atualizar agora",
	"Quit": "Sair",
	"Claude — 5h: {percent} — {reset}": "Claude — 5h: {percent} — {reset}",
	"7 days": "7 dias",
	"7 days ({model})": "7 dias ({model})",
	"{percent} ({used} h / {elapsed} h elapsed)": "{percent} ({used} h / {elapsed} h decorridas)",
	"{percent} ({used} d / {elapsed} d elapsed)": "{percent} ({used} d / {elapsed} d decorridos)",
	".": ",",
	"{label}: {percent} — {reset}": "{label}: {percent} — {reset}",
	"Claude usage": "Uso do Claude",
	"Claude — session expired": "Claude — sessão expirada",
	"Claude — error": "Claude — erro",
	"claude-usage-tray error": "Erro do claude-usage-tray",
}
