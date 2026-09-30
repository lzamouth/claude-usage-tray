#!/usr/bin/env bash
# Set up the virtualenv and register claude-usage-tray to start with the session.
#
#   ./install.sh            autostart entry (~/.config/autostart), the default
#   ./install.sh --systemd  systemd user service (restarts on crash)
#   ./install.sh --no-start only create the virtualenv
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE="${1:---autostart}"

render() {
	# Fill the @APP_DIR@ placeholder of a packaging template.
	sed "s|@APP_DIR@|${APP_DIR}|g" "${APP_DIR}/packaging/$1.in" > "$2"
}

if [[ ! -x "${APP_DIR}/.venv/bin/python" ]]; then
	# --system-site-packages: python3-gi comes from the distribution.
	python3 -m venv --system-site-packages "${APP_DIR}/.venv"
fi
"${APP_DIR}/.venv/bin/pip" install --quiet -r "${APP_DIR}/requirements.txt"

case "${MODE}" in
	--autostart)
		mkdir -p "${HOME}/.config/autostart"
		render claude-usage-tray.desktop "${HOME}/.config/autostart/claude-usage-tray.desktop"
		echo "Autostart entry installed: ~/.config/autostart/claude-usage-tray.desktop"
		;;
	--systemd)
		mkdir -p "${HOME}/.config/systemd/user"
		render claude-usage-tray.service "${HOME}/.config/systemd/user/claude-usage-tray.service"
		systemctl --user daemon-reload
		systemctl --user enable --now claude-usage-tray.service
		echo "systemd user service enabled: claude-usage-tray.service"
		;;
	--no-start)
		;;
	*)
		echo "Usage: $0 [--autostart | --systemd | --no-start]" >&2
		exit 2
		;;
esac
